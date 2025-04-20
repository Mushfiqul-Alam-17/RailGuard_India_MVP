import os
import logging
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.feature_extraction.text import CountVectorizer
import pickle
import re

logger = logging.getLogger(__name__)

# Initialize and train a simple model
# In production, this would be a properly trained model
def initialize_model():
    """Initialize a simple AI model for complaint analysis"""
    # Mock training data
    complaints = [
        "TT asked for money without giving receipt",
        "I was fined without any reason",
        "TT demanded cash and refused to give receipt",
        "TT threatened me for not having proper ticket",
        "Train was late by 2 hours",
        "AC was not working in my coach",
        "Food quality was poor",
        "Toilet was dirty",
        "My seat was occupied by someone else",
        "TT forced me to pay extra",
        "TT charged me extra for luggage without measuring",
        "TT issued fine without checking my ticket properly",
        "No water in toilet",
        "Train was overcrowded",
        "Standing passengers not allowed in reserved coach"
    ]
    
    # Labels (high risk = 1, low risk = 0)
    labels = [1, 1, 1, 1, 0, 0, 0, 0, 0, 1, 1, 1, 0, 0, 0]
    
    # Create a bag of words model
    vectorizer = CountVectorizer()
    X = vectorizer.fit_transform(complaints)
    
    # Train a Random Forest model
    model = RandomForestClassifier(n_estimators=10, random_state=42)
    model.fit(X, labels)
    
    return vectorizer, model

# Initialize the model and vectorizer
vectorizer, complaint_model = initialize_model()

def analyze_complaint_risk(complaint_text):
    """
    Analyze complaint text to determine risk level
    
    Args:
        complaint_text (str): Complaint message
        
    Returns:
        str: Risk level ('High' or 'Low')
    """
    try:
        # Check for key risk words
        high_risk_keywords = ['money', 'cash', 'bribe', 'receipt', 'fine', 'illegal', 'extra', 'demanded', 'threatened']
        
        # Preprocess text
        complaint_text = complaint_text.lower()
        
        # Direct keyword matching for high-risk terms
        for keyword in high_risk_keywords:
            if keyword in complaint_text:
                logger.info(f"High risk keyword '{keyword}' found in complaint")
                return "High"
        
        # Use the model for more nuanced prediction
        X = vectorizer.transform([complaint_text])
        prediction = complaint_model.predict(X)[0]
        
        risk_level = "High" if prediction == 1 else "Low"
        logger.info(f"AI model predicted risk level: {risk_level}")
        
        return risk_level
    
    except Exception as e:
        logger.error(f"Error analyzing complaint risk: {str(e)}")
        # Default to low risk in case of error
        return "Low"

def predict_seat_reallocation(coach, vacant_seats):
    """
    Predict if seat reallocation is needed
    
    Args:
        coach (str): Coach number
        vacant_seats (int): Number of vacant seats
        
    Returns:
        bool: True if reallocation recommended
    """
    # Simple rule-based decision for MVP
    # In production, this would use a more sophisticated model
    return vacant_seats >= 2

def analyze_fraud_patterns(complaints, fines):
    """
    Analyze fraud patterns across complaints and fines
    
    Args:
        complaints (list): List of complaint objects
        fines (list): List of fine objects
        
    Returns:
        dict: Fraud analysis results
    """
    # Count high risk complaints by phone
    high_risk_counts = {}
    for complaint in complaints:
        if complaint.risk_level == "High":
            high_risk_counts[complaint.phone] = high_risk_counts.get(complaint.phone, 0) + 1
    
    # Identify potential fraudsters (3+ high risk complaints)
    potential_fraudsters = {phone: count for phone, count in high_risk_counts.items() if count >= 3}
    
    # Analyze fine patterns
    fine_counts = {}
    for fine in fines:
        fine_counts[fine.phone] = fine_counts.get(fine.phone, 0) + 1
    
    # Cross-reference with high risk complaints
    fraud_risk = {}
    for phone, fine_count in fine_counts.items():
        if phone in high_risk_counts:
            high_risk_count = high_risk_counts[phone]
            fraud_risk[phone] = (fine_count, high_risk_count)
    
    return {
        "potential_fraudsters": potential_fraudsters,
        "fraud_risk": fraud_risk
    }
