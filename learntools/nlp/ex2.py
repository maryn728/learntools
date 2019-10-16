import random

import numpy as np
import pandas as pd
import spacy
from spacy.util import minibatch
import textwrap

from learntools.core import *

def load_data(csv_file, split=0.8):
    data = pd.read_csv(csv_file)
    
    # Shuffle data
    train_data = data.sample(frac=1, random_state=7)
    
    texts = train_data.text.values
    labels = [{"POSITIVE": bool(y), "NEGATIVE": not bool(y)}
              for y in train_data.sentiment.values]
    split = int(len(train_data) * split)
    
    train_labels = [{"cats": labels} for labels in labels[:split]]
    val_labels = [{"cats": labels} for labels in labels[split:]]
    
    return texts[:split], train_labels, texts[split:], val_labels

train_texts, train_labels, val_texts, val_labels = load_data('../input/nlp-course/yelp_ratings.csv')

def create_model():
    # Create an empty model
    nlp = spacy.blank("en")

    # Create the TextCategorizer with exclusive classes and "bow" architecture
    textcat = nlp.create_pipe(
                "textcat",
                config={
                    "exclusive_classes": True,
                    "architecture": "bow"})
    nlp.add_pipe(textcat)

    # Add NEGATIVE and POSITIVE labels to text classifier
    textcat.add_label("NEGATIVE")
    textcat.add_label("POSITIVE")

    return nlp

def train_func(model, train_data, optimizer, batch_size=8):
    losses = {}
    # random.seed(1)
    random.shuffle(train_data)
    batches = minibatch(train_data, size=batch_size)
    for batch in batches:
        texts, labels = zip(*batch)
        model.update(texts, labels, sgd=optimizer, losses=losses)
    return losses

class CreateTextCatModel(CodingProblem):
    _var = 'nlp'
    _hint = ("After creating the empty model, use .create_pipe to add the TextCategorizer "
             "to the nlp model. Set the config appropriately for exclusive classes and bow "
             "architecture. Then use .add_label to add labels.")
    _solution = CS("""
    # Create an empty model
    nlp = spacy.blank("en")

    # Create the TextCategorizer with exclusive classes and "bow" architecture
    textcat = nlp.create_pipe(
                "textcat",
                config={
                    "exclusive_classes": True,
                    "architecture": "bow"})
    nlp.add_pipe(textcat)

    # Add NEGATIVE and POSITIVE labels to text classifier
    textcat.add_label("NEGATIVE")
    textcat.add_label("POSITIVE")
    """)

    def check(self, nlp):
        assert nlp.has_pipe('textcat'), "Please add a TextCategorizer to the model's pipeline"

        textcat = nlp.get_pipe('textcat')
        message = f"TextCatagorizer labels should be ('NEGATIVE', 'POSITIVE'), we found {textcat.labels}"
        assert textcat.labels == ('NEGATIVE', 'POSITIVE'), message

        config = textcat.cfg
        assert config['architecture'] == 'bow', "Please use the 'bow' architecture"
        assert config['exclusive_classes'], "Be sure to set exclusive_classes to True in the model config"


class TrainFunction(CodingProblem):
    _var = 'train'
    _hint = ("Use minibatch to create the batches. You can use the zip method to split the "
             "train_data list into two separate lists. For training the model, model.update "
             "takes the texts and labels. Be sure to use a batch size of 8, and dropout 0.2")
    _solution = CS("""
    def train(model, train_data, optimizer, batch_size=8):
        losses = {}
        random.shuffle(train_data)
        batches = minibatch(train_data, size=batch_size)
        for batch in batches:
            texts, labels = zip(*batch)
            model.update(texts, labels, sgd=optimizer, losses=losses)
        return losses""")

    def check(self, train):
        
        def soln_func(model, train_data, optimizer, batch_size=8):
            losses = {}
            #random.seed(1)
            random.shuffle(train_data)
            batches = minibatch(train_data, size=batch_size)
            for batch in batches:
                texts, labels = zip(*batch)
                model.update(texts, labels, sgd=optimizer, losses=losses)
            return losses
        

        train_data = list(zip(train_texts, train_labels))
        
        spacy.util.fix_random_seed(1)
        random.seed(1)
        nlp = create_model()
        optimizer = nlp.begin_training()
        student_losses = train(nlp, train_data[:1000], optimizer)

        spacy.util.fix_random_seed(1)
        random.seed(1)
        nlp = create_model()
        optimizer = nlp.begin_training()
        soln_losses = soln_func(nlp, train_data[:1000], optimizer)

        assert student_losses == soln_losses, "Your loss isn't the same as our solution. Make sure to set batch size to 8 and dropout to 0.2."

class PredictFunction(CodingProblem):
    _var = 'predict'
    _hint = ("You can use model.tokenizer on each text example to tokenize the input data. "
             "To make predictions, you want to get the TextCategorizer object from the model "
             "with model.get_pipe. The use .predict on the TextCategorizer to get the scores. "
             "With the scores array, the .argmax method will return the index of the highest "
             "value. Take note of the axis argument in .argmax so you're finding the max index "
             "for each example")
    _solution = CS("""
        def predict(model, texts):
            # Use the tokenizer to tokenize each input text example
            docs = [model.tokenizer(text) for text in texts]
            
            # Use textcat to get the scores for each doc
            textcat = model.get_pipe('textcat')
            scores, _ = textcat.predict(docs)
            
            # From the scores, find the class with the highest score/probability
            predicted_class = scores.argmax(axis=1)

            return predicted_class""")

    def check(self, predict):
        
        def soln_func(model, texts):
            # Use the tokenizer to tokenize each input text example
            docs = [model.tokenizer(text) for text in texts]
            
            # Use textcat to get the scores for each doc
            textcat = model.get_pipe('textcat')
            scores, _ = textcat.predict(docs)
            
            # From the scores, find the class with the highest score/probability
            predicted_class = scores.argmax(axis=1)

            return predicted_class

        spacy.util.fix_random_seed(1)
        nlp = create_model()
        optimizer = nlp.begin_training()
        train_data = list(zip(train_texts, train_labels))
        _ = train_func(nlp, train_data[:1000], optimizer)
        student_predicted = predict(nlp, val_texts[20:30])
        soln_predicted = soln_func(nlp, val_texts[20:30])

        assert np.all(student_predicted == soln_predicted)

class EvaluateFunction(CodingProblem):
    _var = 'evaluate'
    _hint = ("Use your predict function to get the predicted classes. "
             "The labels look like `{'cats': {'POSITIVE':True, 'NEGATIVE': False}}`, "
             "you'll need to convert these into 1s where POSITIVE is True, and 0 where "
             "POSITIVE is False. Once you have the predictions and true classes, calculate "
             "the accuracy")
    _solution = CS("""
    def evaluate(model, texts, labels):
        # Get predictions from textcat model
        predicted_class = predict(model, texts)
        
        # From labels, get the true class as a list of integers (POSITIVE -> 1, NEGATIVE -> 0)
        true_class = [int(each['cats']['POSITIVE']) for each in labels]
        
        # A boolean or int array indicating correct predictions
        correct_predictions = predicted_class == true_class
        
        # The accuracy, number of correct predictions divided by all predictions
        accuracy = correct_predictions.mean()
        
        return accuracy
    """)

    def check(self, evaluate):
        def soln_func(model, texts, labels):

            def predict (model, texts):
                docs = [model.tokenizer(text) for text in texts]
                textcat = model.get_pipe('textcat')
                scores, _ = textcat.predict(docs)
                return scores.argmax(axis=1)

            # Get predictions from textcat model
            predicted_class = predict(model, texts)
            # From labels, get the true class as a list of integers (POSITIVE -> 1, NEGATIVE -> 0)
            true_class = [int(each['cats']['POSITIVE']) for each in labels]
            # A boolean or int array indicating correct predictions
            correct_predictions = predicted_class == true_class
            # The accuracy, number of correct predictions divided by all predictions
            accuracy = correct_predictions.mean()
            return accuracy

        spacy.util.fix_random_seed(1)
        nlp = create_model()
        optimizer = nlp.begin_training()
        train_data = list(zip(train_texts, train_labels))
        _ = train_func(nlp, train_data[:1000], optimizer)
        student_acc = evaluate(nlp, val_texts[:30], val_labels[:30])
        soln_acc = soln_func(nlp, val_texts[:30], val_labels[:30])

        assert np.all(student_acc == soln_acc)

class ModelOptimizationQuestion(ThoughtExperiment):
    _solution = ("Answer: There are various hyperparameters to work with here. The biggest one "
                 "is the TextCategorizer architecture. You used the simplest model which trains "
                 "faster but likely has worse performance than the CNN and ensemble models. You "
                 "can adjust the dropout parameter to reduce overfitting. Also, you can save the "
                 "model after each training pass through the data and use the model with the best "
                 "validation accuracy.")

qvars = bind_exercises(globals(), [
    CreateTextCatModel,
    TrainFunction,
    PredictFunction,
    EvaluateFunction,
    ModelOptimizationQuestion
    ],
    tutorial_id=262,
    var_format='q_{n}',
    )
__all__ = list(qvars)