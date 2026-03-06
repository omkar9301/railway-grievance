import pickle
import random
import re

model = pickle.load(open("model.pkl","rb"))
vectorizer = pickle.load(open("vectorizer.pkl","rb"))
intents = pickle.load(open("intents.pkl","rb"))

class SmartChatbot:

    def predict_intent(self,message):

        X = vectorizer.transform([message])
        intent = model.predict(X)[0]

        return intent

    def detect_complaint_id(self,message):

        match = re.search(r'\d+',message)

        if match:
            return match.group()

        return None

    def generate_response(self,message):

        intent = self.predict_intent(message)

        complaint_id = self.detect_complaint_id(message)

        if intent == "track" and complaint_id:
            return f"I found complaint ID {complaint_id}. Checking status..."

        for i in intents["intents"]:
            if i["tag"] == intent:
                return random.choice(i["responses"])

        return "Sorry I didn't understand."