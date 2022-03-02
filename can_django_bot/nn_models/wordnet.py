from collections import Counter

import pandas as pd
import numpy as np

import nltk
from nltk.tokenize import sent_tokenize, word_tokenize
import catboost
from pymystem3 import Mystem
import pymorphy2
from nltk.stem.snowball import SnowballStemmer 

from typing import Any

import warnings
warnings.filterwarnings('ignore')

from django.conf import settings

class WordNetReviewGenerator:
    """
        Глобальный класс для нахождения полезных биграмм в отзывах
        и формирования на их основе итогового отчета 
    """
    
    def __init__(self, clf:catboost.CatBoostClassifier, extractor:Any, emb_model:Any, context:Any, user:Any, message_id:int):
        """
            Обработка инициализации экземпляра класса
            @clf - классификатор градиентного бустинга
            @raw_data - 'сырые' данные
            @extractor - RUSentimentExtractor модель или любая другая модель
            @emb_model -  модель для получения русского эмбеддинга
            @context - контекст телеграм, где лежит бот, куда будем слать сообщения о процессе
            @user - пользователь, для которого работает wordnet
            @message_id - id сообщения, которое будет редачиться по мере анализа
        """
        
        self.clf = clf
        self.extractor = extractor
        self.russian_stopwords = nltk.corpus.stopwords.words("russian")
        self.lemmer = Mystem()
        self.morph = pymorphy2.MorphAnalyzer()
        self.emb_model = emb_model
        self.stemmer = SnowballStemmer("russian")

        self.context = context
        self.user = user
        self.message_id = message_id
        
    def run(self, raw_data:pd.DataFrame):
        """
            Функция запуска алгоритма
        """
        self.raw_data = raw_data
        self.data_prep()
        
        self.context.bot.edit_message_text(
                    chat_id=self.user.external_id,
                    message_id=self.message_id,
                    text='🪓 Предобработал собранные данные.'
                )
        
        self.bigrams_work()

        self.context.bot.edit_message_text(
                    chat_id=self.user.external_id,
                    message_id=self.message_id,
                    text='⚱️ Выделил полезные топики.'
                )
        
        self.classification()
        
        self.context.bot.edit_message_text(
                    chat_id=self.user.external_id,
                    message_id=self.message_id,
                    text='🧽 Классифицировал значимые топики.'
                )

        return self.output()
        
    def output(self) -> None:
        def prepare_category(t:str, keywords:Any, good_cls:Any):
            """
                Функция подготовки массива данных по тональности
                'pos' - позитивная, 'neg' - негативная
                
                @t - тип тональности
                @keywords - те биграммы, которые прошли фильтр и классификацию
                @good_cls - пласт отзывов
            """
            
            end_data = {}
            garbage = {}

            if self.raw_data.shape[0] <= 100:
                lower_por = 0
                upper_por = 10
            elif t == 'pos':
                if self.raw_data.shape[0] > 100 and self.raw_data.shape[0] <= 1500:
                    lower_por = 2
                    upper_por = 10
                elif self.raw_data.shape[0] > 1500:
                    lower_por = 3
                    upper_por = 10
            else:
                if self.raw_data.shape[0] > 100 and self.raw_data.shape[0] <= 1500:
                    lower_por = 0
                    upper_por = 100
                elif self.raw_data.shape[0] > 1500:
                    lower_por = 1
                    upper_por = 100
                
            for w in keywords:        
                rate = []
                vals = []

                for row in good_cls.values:
                        if t == 'neg':
                            for sent in sent_tokenize(row[0]):
                                if w in self.remove_every(sent.lower()).strip():
                                    rate.append(row[1])
                                    vals.append(sent)
                        else:
                            for sent in sent_tokenize(row[0]):
                                if w in self.remove_every(sent.lower()).strip():
                                    rate.append(row[1])
                                    vals.append(sent)

                if self.stemmer.stem(w.split()[1]) not in settings.BANNED_ADJ_STEMMED:
                    if len(vals) > lower_por and len(vals) < upper_por:
                        vals = vals[:4]
                        rate = rate[:4] 

                        n, a = w.split()
                        try:
                            gender = self.morph.parse(n)[0].gender
                            a = a.inflect({gender, 'sing'})
                        except:
                            pass
                        
                        w = self.morph.parse(n)[0].normal_form + " " + a
                        if (t == 'neg' and np.array(rate).mean() > 3) or (t == 'pos' and np.array(rate).mean() <=3):
                            if w in garbage.keys():
                                    garbage[w]['examples'] += vals
                                    garbage[w]['rates'] += rate

                            else:
                                garbage[w] = {
                                    'examples':vals,
                                    'rates':rate,
                                }

                        else:    
                            if w in end_data.keys():
                                    end_data[w]['examples'] += vals
                                    end_data[w]['rates'] += rate

                            else:
                                end_data[w] = {
                                    'examples':vals,
                                    'rates':rate,
                                }


            for kwd in end_data.keys():
                end_data[kwd]['mean_rate'] = np.round(np.mean(end_data[kwd]['rates']), 2)


            return end_data, garbage
        
        bad_report, garb_neg = prepare_category('neg', self.end_neg, self.data)
        good_report, garb_pos = prepare_category('pos', self.end_pos, self.data)

        end_report = {
            'good_points':{**good_report, **garb_neg},
            'bad_points':{**bad_report, **garb_pos}
        }
        
        return end_report
        
    def classification(self) -> None:
        """
            Функция классификации биграм
        """
        
        sent_filtered = pd.DataFrame({'text':self.pos_clf_prepared})
        sent_filtered['emb'] = sent_filtered['text'].apply(lambda x: self.extractor.get_text_embedding(text=x, model=self.emb_model, vector_size=300))

        sent_filtered['pred'] = self.clf.predict(np.stack(sent_filtered['emb']))
        self.end_pos = list(sent_filtered[sent_filtered['pred'] == 1]['text'].values)
        
        sent_filtered = pd.DataFrame({'text':self.neg_clf_prepared})
        sent_filtered['emb'] = sent_filtered['text'].apply(lambda x: self.extractor.get_text_embedding(text=x, model=self.emb_model, vector_size=300))

        sent_filtered['pred'] = self.clf.predict(np.stack(sent_filtered['emb']))
        self.end_neg = list(sent_filtered[sent_filtered['pred'] == 1]['text'].values)
        
        return None
        
    def bigrams_work(self):
        """
            Функция разделения на биграммы и их классификация
        """
        
        def get_normal_bigrams(text):
            """
                Функция получения только СУЩЕСТВУЮЩИХ в датасете биграм
                @text - текст отзыва
            """
            
            words = word_tokenize(text)
            bigrams = []

            for i in range(len(words) - 1):
                tag1, tag2 = str(self.morph.parse(words[i])[0].tag).split(',')[0], str(self.morph.parse(words[i + 1])[0].tag).split(',')[0]

                if tag2 in ['ADJF','ADJS'] and tag1 == 'NOUN':
                    bigrams.append(words[i] + ' ' + words[i + 1])

            return bigrams
        
        def prep_2_gram(text):
            """
                Функция фильтрации биграмм по содержанию одного из элементов в списке стопслов
                @text - текст двуграммы
        
        
                P.S. Функция нужна для фильтрации в методе filter()
            """
            
            for word in text.split(' '):
                    if self.lemmer.lemmatize(word)[0] in self.russian_stopwords:
                        return False
            return True  
        
        pos_sent_normal = sum([[i for i in get_normal_bigrams(text)] for text in self.pos], [])
        neg_sent_normal = sum([[i for i in get_normal_bigrams(text)] for text in self.neg], [])


        pos_sent_normal_filtered = list(filter(prep_2_gram, pos_sent_normal))
        neg_sent_normal_filtered = list(filter(prep_2_gram, neg_sent_normal))

        pos_c = dict(Counter(pos_sent_normal_filtered).items())
        neg_c = dict(Counter(neg_sent_normal_filtered).items())

        self.pos_clf_prepared = list(pd.DataFrame({'text':pos_c.keys(), 'count':pos_c.values()}).sort_values(by='count', ascending=False)['text'])
        self.neg_clf_prepared = list(pd.DataFrame({'text':neg_c.keys(), 'count':neg_c.values()}).sort_values(by='count', ascending=False)['text'])

        return 
        
    def data_prep(self) -> None:
        """
            Функция предобработки сырых и отработанных данных
        """
        
        self.raw_data.set_axis(['review', 'rate', 'created_at'], axis='columns', inplace=True)
        self.raw_data['review'] = self.raw_data['review'].apply(lambda x: x.strip().replace('\n','')) 

        # # в зависимоси от количества элементов нужно выставить пороговые для отбора значения
        if self.raw_data.shape[0] < 1000:
            self.data = self.raw_data.drop(['created_at'], axis='columns')
        else:
            extracted_data = self.extractor.run(pd.DataFrame({'review':self.raw_data['review']}))
            self.data = pd.DataFrame({'review':extracted_data})
        
        self.data['rate'] = self.data['review'].apply(self.get_star)
        self.data['prepared_review'] = self.data['review'].apply(self.remove_every)
        
        # разделим на позитивные и негативные по оценке отзывы
        self.pos = sum([sent_tokenize(text) for text in list(self.data[self.data['rate'] >= 3]['prepared_review'].values)],[])
        self.neg = sum([sent_tokenize(text) for text in list(self.data[self.data['rate'] < 3]['prepared_review'].values)],[])
        
        return None
        
    def remove_every(self,text):
        """
            Вспомогательная функция, помогающая почистить исходный текст от мусора,
            используя статичные методы класса RUSentimentExtractor
        """
        
        return self.extractor.remove_garbage(text)
    
    def get_star(self, text):
        """
            Вспомогательная функция, помогающая найти оценку отзыва в исходном датасете
            @text - текст отзыва
        """

        try:
            review_star = self.raw_data[self.raw_data['review'] == text.strip()]['rate'].values[0]
            return review_star
        except:
            return None
        