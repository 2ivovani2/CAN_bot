import pandas as pd
import numpy as np

import emoji
import re

from catboost import CatBoostClassifier
from navec import Navec

from django.conf import settings

from nltk.tokenize import sent_tokenize, word_tokenize
import pymorphy2
from nltk.stem.snowball import SnowballStemmer
from sklearn.cluster import DBSCAN

class CAN_ML:
    """
        Класс, реализующий ML обработку 
    """
    
    def __init__(self, classifier:CatBoostClassifier, emb_model:Navec, stemmer:SnowballStemmer, morph:pymorphy2.MorphAnalyzer) -> None:
        self.classifier = classifier
        self.emb_model = emb_model
        self.stemmer = stemmer
        self.morph = morph
        
        # константы
        self.pos_eps = 3.5
        self.neg_eps = 2.5
        self.banned_adj =  ['бесполезн', 'отличн', 'бомбов', 'бредов', 'важн', 'взрывн', 'возмутительн', 'гадк', 'гениальн', 'годн', 'друг', 'единствен', 'жалк', 'жив', 'забавн', 'идеальн', 'идентичн', 'изумительн', 'изящн', 'как', 'классн', 'крут', 'лев', 'люб', 'мил', 'модн', 'неверн', 'неплох', 'непохож', 'плох', 'хорош', 'прост', 'готов', 'серьезн', 'супер', 'классн', 'топ', 'бесподобн','очен', 'котор', 'довольн', 'довол']
 
        
    def run(self, data) -> dict:
        """
            Функция последовательного запуска алгоритма 
        """
        
        # удаляем мусор из данных
        data['review_clear'] = data['review'].apply(self.remove_garbage)

        # разделение на позитив и негатив
        pos = sum([sent_tokenize(text) for text in list(data[data['rate'] > 3]['review_clear'].values)],[])
        neg = sum([sent_tokenize(text) for text in list(data[data['rate'] <= 3]['review_clear'].values)],[])        
        
        # получение биграм
        positive_bigrams = self.get_bigrams(pos)   
        negative_bigrams = self.get_bigrams(neg)
    
        # классификация
        positive_bigrams['pred'] = self.classifier.predict(np.stack(positive_bigrams['bigrams_embs'].values))
        negative_bigrams['pred'] = self.classifier.predict(np.stack(negative_bigrams['bigrams_embs'].values))

        positive_classified = positive_bigrams[positive_bigrams['pred'] == 1].drop_duplicates(subset=['bigrams'])
        negative_classified = negative_bigrams[negative_bigrams['pred'] == 1].drop_duplicates(subset=['bigrams'])
    
        # кластеризация
        positive_classified['cluster'] = DBSCAN(eps=3.5, min_samples=1).fit(np.stack(positive_classified['bigrams_embs'])).labels_
        negative_classified['cluster'] = DBSCAN(eps=2.5, min_samples=1).fit(np.stack(negative_classified['bigrams_embs'])).labels_

        positive_df = self.bigrams_clusterization(positive_classified)
        negative_df = self.bigrams_clusterization(negative_classified)
        
        # фильтрация
        positive_df['stemmed_adj'] = positive_df['bigrams'].apply(lambda x: self.stemmer.stem(x.split()[0]))
        positive_df = positive_df[~positive_df['stemmed_adj'].isin(self.banned_adj)]

        negative_df['stemmed_adj'] = negative_df['bigrams'].apply(lambda x: self.stemmer.stem(x.split()[0]))
        negative_df = negative_df[~negative_df['stemmed_adj'].isin(self.banned_adj)]

        positive = pd.DataFrame({})
        for adj in positive_df['stemmed_adj'].unique():
            positive_sample = positive_df[positive_df['stemmed_adj'] == adj].sample(n=1)
            positive = pd.concat([positive, positive_sample])

        negative = pd.DataFrame({})
        for adj in negative_df['stemmed_adj'].unique():
            negative_sample = negative_df[negative_df['stemmed_adj'] == adj].sample(n=1)
            negative = pd.concat([negative, negative_sample])
        
        # подготовка формата данных
        return self.prepare_report_dict(positive['bigrams'].values, negative['bigrams'].values, data)
        
    def bigrams_clusterization(self, classified:pd.DataFrame) -> pd.DataFrame:
        """
            Кластеризация биграмм
        """
        
        df = pd.DataFrame({})

        for cluster in classified['cluster'].unique():
            sample = classified[classified['cluster'] == cluster].sample(n=1)
            df = pd.concat([df, sample])
    
        return df
    
    def get_bigrams(self, reviews:list) -> pd.DataFrame:
        """
            Функция получения биграм из отзывов
        """
        
        bigrams = pd.DataFrame({'bigrams':[], 'bigrams_embs':[]})
        
        for review in reviews:
                normal_bigrams = self.get_normal_bigrams(review)
                embeddings = list(map(lambda x: self.get_text_embedding(x), normal_bigrams))
                bigrams = pd.concat([bigrams, pd.DataFrame({
                    'bigrams':normal_bigrams,
                    'bigrams_embs':embeddings
                })])
        
        return bigrams
    
    @staticmethod
    def prepare_report_dict(pos_bigrams:np.array, neg_bigrams:np.array, dataset:pd.DataFrame) -> dict:
        """
            Функция подготовки структуры данных для генерации отчета
        """
        
        pos_dict = {}
        neg_dict = {}

        pos_reviews = dataset[dataset['rate'] > 3].values
        neg_reviews = dataset[dataset['rate'] <= 3].values

        for review in pos_reviews:
            for bigram in pos_bigrams:
                if bigram in review[2]:
                    if bigram not in pos_dict.keys():
                        pos_dict[bigram] = {
                            'examples':[review[0]],
                            'rates':[review[1]]
                        }
                    else:
                        if len(pos_dict[bigram]['examples']) < 4:
                            pos_dict[bigram]['examples'] += [review[0]]
                            pos_dict[bigram]['rates'] += [review[1]]

        for key in pos_dict.keys():
            pos_dict[key]['mean_rate'] = round(np.mean(pos_dict[key]['rates']), 1)


        for review in neg_reviews:
            for bigram in  neg_bigrams:
                if bigram in review[2]:
                    if bigram not in neg_dict.keys():
                        neg_dict[bigram] = {
                            'examples':[review[0]],
                            'rates':[review[1]]
                        }
                    else:
                        if len(neg_dict[bigram]['examples']) < 4:
                            neg_dict[bigram]['examples'] += [review[0]]
                            neg_dict[bigram]['rates'] += [review[1]]                 

        for key in neg_dict.keys():
            neg_dict[key]['mean_rate'] = round(np.mean(neg_dict[key]['rates']), 1)

        return {
            'good_points':pos_dict,
            'bad_points':neg_dict,
        }
    
    def get_normal_bigrams(self, text:str) -> list:
        """
            Метод получения только СУЩЕСТВУЮЩИХ в датасете биграм
            @text - текст отзыва
        """

        words = word_tokenize(text)
        bigrams = []

        for i in range(len(words) - 1):
            tag1, tag2 = str(self.morph.parse(words[i])[0].tag).split(',')[0], str(self.morph.parse(words[i + 1])[0].tag).split(',')[0]

            if (tag2 in ['ADJF','ADJS'] and tag1 == 'NOUN'):
                bigrams.append(words[i + 1] + ' ' + words[i])
            elif (tag1 in ['ADJF','ADJS'] and tag2 == 'NOUN'):
                 bigrams.append(words[i] + ' ' + words[i + 1])

        return bigrams
    
    @staticmethod
    def remove_garbage(text: str) -> str:
        """
            Метод, удаляющая весь мусор из текста
        """
        
        allchars = [str for str in text]
        emoji_list = [c for c in allchars if c in emoji.UNICODE_EMOJI]
        clean_text = ' '.join([str for str in text.split() if not any(i in str for i in emoji_list)])

        return re.sub(r'\d', ' ', re.sub(r'[^\w\s]',' ',clean_text.strip().lower()))
    
    @staticmethod
    def get_text_embedding(text:str) -> np.array:
        """
            Метод, возвращающий embedding текста
        """
        words = text.split()
        embeddings = []

        for word in words:
            try:
                vector = settings.EMB_MODEL[word.lower()]
            except:
                vector = np.zeros(300)

            embeddings.append(vector)

        return np.array(embeddings).mean(axis=0)