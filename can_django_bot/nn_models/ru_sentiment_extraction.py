import pandas as pd
import numpy as np

import re
import emoji

from sklearn.cluster import DBSCAN
from sklearn.cluster import KMeans

from toolz import pipe

class RUSentimentExtractor:
    """
        Класс, с помощью которого реализуется весь алгоритм вычленения полезных текстов для русского языка
    """
    
    def __init__(self, vectorizer, classifier, cls_eps:float=0.2, cls_metric:str='cosine', cls_min_samples:int=1, vector_size:int=300) -> None:
        self.vectorizer = vectorizer
        self.classifier = classifier
        self.cls_eps = cls_eps
        self.cls_metric = cls_metric
        self.cls_min_samples = cls_min_samples
        self.vector_size = vector_size
        
    def run(self, data:pd.DataFrame) -> np.array:
        """
            Функция, запускающая алгоритм
        """
        
        # каскадно вызовем все необходимые методы
        useful_texts = pipe(data, self.data_prep, self.clusterization, self.cluster_classification, self.text_classification)
        
        return useful_texts
        
    def data_prep(self, df: pd.DataFrame) -> pd.DataFrame:
        """
            Функция, которая предобрабатывает данные
        """
        
        try:
            # при выгрузке в файл, бывает, что забывают игнорировать индекс и он задается как данная колонка 
            df.drop(['Unnamed: 0'], inplace=True, axis=1)
        except KeyError:
            pass
        
        #удаляем все nan
        df.dropna(inplace=True)
        
        # проверим, чтобы количество колонок было равно 1
        if len(df.columns) > 1:
            raise Exception('Columns amount is not equals to 1')
        
        # изменим название колонки на нужное нам
        df.set_axis(['raw_text'],axis=1, inplace=True) 
        
        # воспользуемся статичными методами для очистки текста
        df['text'] = df['raw_text'].apply(RUSentimentExtractor.remove_garbage)
        
        # добавим воспомгательную колонку
        df['text_len'] = df['text'].apply(lambda x: len(x.split()))
        
        # удаляем однословные выбросы
        df = df[df['text_len'] > 1] 
        
        # запишем в таблицу embeddingи очещенных текстов
        df['emb'] = df['text'].apply(lambda el: RUSentimentExtractor.get_text_embedding(el, self.vectorizer, self.vector_size))
        
        return df
    
    def clusterization(self, data: pd.DataFrame) -> pd.DataFrame:
        """
            Функция, возвращающая датасет с кластерами для дальнейшей их классификации
        """
        
        # найдем оптимальное количество кластеров
        clusters_amount = np.unique(DBSCAN(eps=self.cls_eps, metric=self.cls_metric, min_samples=self.cls_min_samples).fit_predict(np.stack(data['emb'].values))).shape[0]
     
        print('Cluster amount is', clusters_amount, '🥺')
        
        # кластеризуем с помощью метода k средних
        kmeans = KMeans(n_clusters=clusters_amount).fit_predict(np.stack(data['emb'].values))
        
        # присвоим каждому отзыву его кластер
        data['cluster'] = kmeans
    
        #получим сырые кластеры (первоначальный вид) и предобработанные для классификации
        raw_clusters = []
        prep_clusters = []

        for i in np.unique(kmeans):
            raw_clust = data[data['cluster'] == i]['raw_text'].apply(lambda x: x.replace('\n','').strip())
            raw_clusters.append(np.unique(np.array(raw_clust)))

            prep_clust = data[data['cluster'] == i]['text'].apply(lambda x: x.strip().lower())
            prep_clusters.append(np.unique(np.array(prep_clust)))
        
        # приведем кластера к строчному виду
        cls_prep = list(map(lambda x:' '.join(x), prep_clusters))
        cls_prep_to_clf = list(map(lambda x:' // '.join(x), prep_clusters))
        cls_raw = list(map(lambda x:' // '.join(x), raw_clusters))
        
        # запишем в dataframe и вернем результат
        processed_data = pd.DataFrame({
            'cls_prep': cls_prep,
            'cls_raw': cls_raw,
            'cls_prep_to_clf': cls_prep_to_clf
        })
        
        return processed_data
        
    def cluster_classification(self, processed_data: pd.DataFrame) -> pd.DataFrame:
        """
            Функция, реализующая классификацию кластеров
        """
        
        # получим embedding предобработанных кластеров
        processed_data['cls_prep_emb'] = processed_data['cls_prep'].apply(lambda el: RUSentimentExtractor.get_text_embedding(el, self.vectorizer, self.vector_size))

        # сделаем предсказания
        preds = self.classifier.predict(np.stack(processed_data['cls_prep_emb'].values))
        
        # запишем в наши данные
        processed_data['preds'] = preds
        
        # получим хорошие предсказания
        good_cls = processed_data[processed_data['preds'] == 1]
        
        return good_cls
    
    def text_classification(self, good_cls: pd.DataFrame) -> np.array:
        """
            Функция, реализующая классификацию отдельных текстов,
            входящих в хорошие кластера
        """
         
        # функция перевода кластера в отдельные элементы
        def cls_to_text(series: pd.Series) -> np.array:
            end = np.array([])
            for val in list(series.values):
                end = np.concatenate((end, np.array(val.split(' // '))), axis=None)
            return end    
        
        cls_to_clf = cls_to_text(good_cls['cls_prep_to_clf'])
        cls_to_raw = cls_to_text(good_cls['cls_raw'])
        
        if cls_to_clf.shape[0] > cls_to_raw.shape[0]:
            cls_to_clf = cls_to_clf[:cls_to_raw.shape[0]] 
        
        if cls_to_raw.shape[0] > cls_to_clf.shape[0]:
            cls_to_raw = cls_to_raw[:cls_to_clf.shape[0]] 
        
        # запишем все в dataframe
        useful_texts = pd.DataFrame({
            'useful_text': cls_to_clf,
            'useful_text_raw': cls_to_raw
        })
        
        # записываем embedding каждого полезного отзыва
        useful_texts['emb'] = useful_texts['useful_text'].apply(lambda x: RUSentimentExtractor.get_text_embedding(x, self.vectorizer, self.vector_size))
        
        # делаем предсказания
        preds = self.classifier.predict(np.stack(useful_texts['emb'].values))
        
        # записываем в отдельную колонку
        useful_texts['preds'] = preds
        
        # берем хорошие тексты
        good_texts = useful_texts[useful_texts['preds'] == 1]['useful_text_raw'].values
        
        return good_texts
        
    @staticmethod   
    def get_text_embedding(text: str, model, vector_size:int) -> np.array:
        """
            Функция возвращающая embedding текста
        """
        
        embeddings = []

        text_prepared = [word.lower() for word in text.split()]

        for word in text_prepared:
            try:
                vector = model[word]
                embeddings.append(vector)
            except:
                vector = np.zeros(vector_size)
                embeddings.append(vector)

        return np.array(embeddings).mean(axis=0)    
    
    @staticmethod
    def remove_garbage(text: str) -> str:
        """
            Метод, удаляющий весь мусор из текста
        """
        
        allchars = [str for str in text]
        emoji_list = [c for c in allchars if c in emoji.UNICODE_EMOJI]
        clean_text = ' '.join([str for str in text.split() if not any(i in str for i in emoji_list)])

        return re.sub(r'\d', '', re.sub(r'[^\w\s]','',clean_text.strip().lower()))
    
   