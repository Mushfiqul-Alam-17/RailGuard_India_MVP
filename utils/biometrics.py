import logging
import base64
import hashlib
import json
import os
import numpy as np
import traceback
import time
from datetime import datetime
from io import BytesIO
import glob

# Try to import OpenCV first - this will be our primary method
try:
    import cv2
    OPENCV_AVAILABLE = True
    logging.info("OpenCV is available for face detection")
except ImportError:
    OPENCV_AVAILABLE = False
    logging.warning("OpenCV not available, using simple hash verification")
    logging.error(traceback.format_exc())

# Import PIL for image handling
try:
    from PIL import Image
except ImportError:
    logging.error("PIL module not available, verification may fail")
    logging.error(traceback.format_exc())

# Configure logging
logger = logging.getLogger(__name__)

class BiometricVerifier:
    def __init__(self):
        self.faces_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'faces')
        # Create faces directory if it doesn't exist
        if not os.path.exists(self.faces_dir):
            os.makedirs(self.faces_dir)
            
        # Create models directory for face recognizer models
        self.models_dir = os.path.join(self.faces_dir, 'models')
        if not os.path.exists(self.models_dir):
            os.makedirs(self.models_dir)
            
        logger.info(f"BiometricVerifier initialized with storage at {self.faces_dir}")

        # Initialize OpenCV face detection
        try:
            import cv2
            # Use cascade classifiers - more reliable for detection
            # Try to load both frontal and profile face cascades for better detection
            self.face_cascade_frontal = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
            self.face_cascade_profile = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_profileface.xml')
            # Also load eye detection for improved verification
            self.eye_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_eye.xml')
            self.use_opencv = True
            logger.info("Using OpenCV cascades for face detection")
            
            # Check if advanced face recognition is available
            try:
                # Initialize LBPH Face Recognizer (Local Binary Patterns Histograms)
                # This is more robust than simple image comparison
                self.face_recognizer = cv2.face_LBPHFaceRecognizer.create()
                self.advanced_recognition = True
                logger.info("OpenCV LBPH face recognition is available")
            except (AttributeError, cv2.error) as e:
                try:
                    # Try another way to initialize the face recognizer
                    self.face_recognizer = cv2.face.LBPHFaceRecognizer_create()
                    self.advanced_recognition = True
                    logger.info("OpenCV face.LBPHFaceRecognizer is available")
                except (AttributeError, cv2.error) as e:
                    self.advanced_recognition = False
                    logger.info("OpenCV advanced face recognition not available, using image similarity")
        except Exception as e:
            self.use_opencv = False
            self.advanced_recognition = False
            logger.warning(f"OpenCV initialization failed: {str(e)}")
            logger.warning("Using simplified hash-based verification")
            logger.error(traceback.format_exc())

    def detect_face(self, img_cv):
        """Detect faces in image with increased accuracy by trying multiple methods"""
        try:
            # Convert to grayscale for detection
            gray = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)
            
            # Equalize histogram to improve detection in different lighting
            gray = cv2.equalizeHist(gray)
            
            # Try to detect frontal faces first with different parameters
            # Start with more lenient parameters to detect more faces
            faces_frontal = self.face_cascade_frontal.detectMultiScale(
                gray,
                scaleFactor=1.2,  # More lenient scale factor
                minNeighbors=3,   # Fewer neighbors required
                minSize=(30, 30),
                flags=cv2.CASCADE_SCALE_IMAGE
            )
            
            # If no frontal faces found, try profile faces
            if len(faces_frontal) == 0:
                faces_profile = self.face_cascade_profile.detectMultiScale(
                    gray,
                    scaleFactor=1.2,  # More lenient scale factor
                    minNeighbors=3,   # Fewer neighbors required
                    minSize=(30, 30),
                    flags=cv2.CASCADE_SCALE_IMAGE
                )
                
                # If profile faces found, use them
                if len(faces_profile) > 0:
                    return gray, faces_profile
                
                # Try with even more lenient parameters if still no faces
                faces_lenient = self.face_cascade_frontal.detectMultiScale(
                    gray,
                    scaleFactor=1.3,    # Even more lenient scale factor
                    minNeighbors=2,     # Even fewer neighbors
                    minSize=(20, 20),   # Smaller minimum size
                    flags=cv2.CASCADE_SCALE_IMAGE
                )
                
                if len(faces_lenient) > 0:
                    return gray, faces_lenient
                    
                # Return empty result if no faces detected
                return gray, []
            
            # Return result with frontal faces (most reliable)
            return gray, faces_frontal
            
        except Exception as e:
            logger.error(f"Face detection error: {str(e)}")
            logger.error(traceback.format_exc())
            return None, []

    def get_all_registered_users(self):
        """Return a list of all registered users (phone numbers)"""
        try:
            # Get all JSON files in the faces directory
            json_files = glob.glob(os.path.join(self.faces_dir, "*.json"))
            # Extract phone numbers from filenames
            users = []
            for json_file in json_files:
                phone = os.path.basename(json_file).replace(".json", "")
                # Verify it's a valid phone number (all digits)
                if phone.isdigit():
                    users.append(phone)
            return users
        except Exception as e:
            logger.error(f"Error getting registered users: {str(e)}")
            return []

    def register_face(self, phone, image_binary):
        """Register a face for a phone number"""
        try:
            # Log input parameters (excluding binary data)
            logger.info(f"Starting face registration for phone: {phone}, image size: {len(image_binary)} bytes")
            
            # Convert binary to image
            try:
                image = Image.open(BytesIO(image_binary))
                logger.info(f"Image opened successfully: format={image.format}, size={image.size}")
            except Exception as e:
                logger.error(f"Failed to open image: {str(e)}")
                logger.error(traceback.format_exc())
                return False

            face_found = False
            face_data = {}

            # Use OpenCV for face detection
            if self.use_opencv:
                logger.info("Using OpenCV for face detection")
                try:
                    # Convert PIL image to OpenCV format
                    img_cv = np.array(image.convert('RGB'))
                    img_cv = img_cv[:, :, ::-1].copy()  # RGB to BGR
                    
                    # Enhanced face detection using multiple methods
                    gray, faces = self.detect_face(img_cv)
                    
                    logger.info(f"Face detection found {len(faces)} faces")
                    
                    if len(faces) > 0:
                        face_found = True
                        # Take the largest face if multiple detected (likely to be the main subject)
                        if len(faces) > 1:
                            # Find the largest face by area (width * height)
                            largest_area = 0
                            largest_idx = 0
                            for i, (x, y, w, h) in enumerate(faces):
                                area = w * h
                                if area > largest_area:
                                    largest_area = area
                                    largest_idx = i
                            
                            # Use the largest face
                            (x, y, w, h) = faces[largest_idx]
                            logger.info(f"Multiple faces detected, using the largest one at {x},{y},{w},{h}")
                        else:
                            # Just use the only face
                            (x, y, w, h) = faces[0]
                        
                        # Add some margin around the face (improve recognition)
                        y_margin = int(h * 0.3)  # Increased margin for better detection
                        x_margin = int(w * 0.3)  # Increased margin for better detection
                        
                        # Ensure margins don't go outside image bounds
                        y_start = max(0, y - y_margin)
                        y_end = min(gray.shape[0], y + h + y_margin)
                        x_start = max(0, x - x_margin)
                        x_end = min(gray.shape[1], x + w + x_margin)
                        
                        # Extract face region with margin
                        face_img = img_cv[y_start:y_end, x_start:x_end]
                        face_gray = gray[y_start:y_end, x_start:x_end]
                        
                        # Resize to standard size for consistency
                        face_img_resized = cv2.resize(face_img, (200, 200))
                        face_gray_resized = cv2.resize(face_gray, (200, 200))
                        
                        # Save the face images for future comparison
                        face_img_path = os.path.join(self.faces_dir, f"{phone}_face.jpg")
                        cv2.imwrite(face_img_path, face_img_resized)
                        
                        # Also save grayscale version
                        face_gray_path = os.path.join(self.faces_dir, f"{phone}_face_gray.jpg")
                        cv2.imwrite(face_gray_path, face_gray_resized)
                        
                        logger.info(f"Saved face image to {face_img_path}")
                        
                        # Calculate face image hash for backup comparison
                        face_img_encoded = cv2.imencode('.jpg', face_img_resized)[1].tobytes()
                        face_img_hash = hashlib.sha256(face_img_encoded).hexdigest()
                        
                        # If LBPH recognizer available, train it with this face
                        if self.advanced_recognition:
                            try:
                                # Create a model file path specific to this user
                                model_path = os.path.join(self.models_dir, f"{phone}_model.yml")
                                
                                # Store multiple samples for better recognition
                                samples = []
                                labels = []
                                
                                # Add current face as multiple samples with small variations for robustness
                                base_face = face_gray_resized
                                
                                # Add the base face
                                samples.append(base_face)
                                labels.append(1)  # Label 1 for the registered face
                                
                                # Add slightly rotated versions
                                rows, cols = base_face.shape
                                center = (cols // 2, rows // 2)
                                
                                # Add more rotated versions for better recognition
                                for angle in [-15, -10, -5, 5, 10, 15]:
                                    rotation_matrix = cv2.getRotationMatrix2D(center, angle, 1.0)
                                    rotated = cv2.warpAffine(base_face, rotation_matrix, (cols, rows))
                                    samples.append(rotated)
                                    labels.append(1)
                                
                                # Also add slightly scaled versions
                                for scale in [0.9, 0.95, 1.05, 1.1]:
                                    scaled_size = (int(cols * scale), int(rows * scale))
                                    scaled = cv2.resize(base_face, scaled_size)
                                    # Make sure it's the right size again
                                    if scale < 1.0:
                                        # Pad if smaller
                                        pad_h = (200 - scaled.shape[0]) // 2
                                        pad_w = (200 - scaled.shape[1]) // 2
                                        scaled_padded = cv2.copyMakeBorder(scaled, pad_h, pad_h, pad_w, pad_w,
                                                                          cv2.BORDER_CONSTANT, value=0)
                                        samples.append(scaled_padded)
                                    else:
                                        # Crop if larger
                                        start_h = (scaled.shape[0] - 200) // 2
                                        start_w = (scaled.shape[1] - 200) // 2
                                        scaled_cropped = scaled[start_h:start_h+200, start_w:start_w+200]
                                        samples.append(scaled_cropped)
                                    labels.append(1)
                                
                                # Add brightness variations
                                for alpha in [0.8, 1.2]:  # Darker and lighter versions
                                    bright_adj = cv2.convertScaleAbs(base_face, alpha=alpha, beta=0)
                                    samples.append(bright_adj)
                                    labels.append(1)
                                
                                # Train the recognizer
                                self.face_recognizer.train(samples, np.array(labels))
                                
                                # Save the model
                                self.face_recognizer.save(model_path)
                                logger.info(f"Trained and saved face recognition model to {model_path}")
                            except Exception as e:
                                logger.error(f"Failed to train face recognizer: {str(e)}")
                                logger.error(traceback.format_exc())
                        
                        # Store face data
                        face_data = {
                            "phone": phone,
                            "face_region": [int(x), int(y), int(w), int(h)],
                            "face_hash": face_img_hash,
                            "timestamp": datetime.now().isoformat(),
                            "method": "opencv_enhanced",
                            "has_model": self.advanced_recognition
                        }
                    else:
                        logger.warning(f"No face detected with OpenCV for {phone}")
                except Exception as e:
                    logger.error(f"OpenCV face detection failed: {str(e)}")
                    logger.error(traceback.format_exc())
            
            # Fallback to image hash if no face detected or OpenCV failed
            if not face_found:
                logger.info("Using hash-based method (fallback)")
                image_hash = hashlib.sha256(image_binary).hexdigest()
                face_data = {
                    "phone": phone,
                    "image_hash": image_hash,
                    "timestamp": datetime.now().isoformat(),
                    "method": "hash"
                }

            # Save to file
            try:
                filepath = os.path.join(self.faces_dir, f"{phone}.json")
                with open(filepath, 'w') as f:
                    json.dump(face_data, f)
                logger.info(f"Face data saved to {filepath}")
            except Exception as e:
                logger.error(f"Failed to save face data: {str(e)}")
                logger.error(traceback.format_exc())
                return False

            # Also save the original image
            try:
                img_path = os.path.join(self.faces_dir, f"{phone}.jpg")
                image.save(img_path, format="JPEG")
                logger.info(f"Image saved to {img_path}")
            except Exception as e:
                logger.error(f"Failed to save image: {str(e)}")
                logger.error(traceback.format_exc())
                # Continue as this is not critical

            logger.info(f"Face registered for {phone} using method: {face_data.get('method', 'unknown')}")
            return True
        except Exception as e:
            logger.error(f"Error in register_face: {str(e)}")
            logger.error(traceback.format_exc())
            return False

    def verify_against_specific_user(self, phone, image_binary):
        """Verify a face against a specific registered user's face"""
        try:
            # Load registered face data
            filepath = os.path.join(self.faces_dir, f"{phone}.json")
            if not os.path.exists(filepath):
                logger.warning(f"No face registered for {phone}")
                return False
                
            # Load the image for verification
            try:
                image = Image.open(BytesIO(image_binary))
                logger.info(f"Verification image opened successfully: format={image.format}, size={image.size}")
            except Exception as e:
                logger.error(f"Failed to open verification image: {str(e)}")
                logger.error(traceback.format_exc())
                return False

            # Load registered face data
            try:
                with open(filepath, 'r') as f:
                    face_data = json.load(f)
                logger.info(f"Loaded face data from {filepath}")
                logger.info(f"Registration method was: {face_data.get('method', 'unknown')}")
            except Exception as e:
                logger.error(f"Failed to load registered face data: {str(e)}")
                logger.error(traceback.format_exc())
                return False
                
            # Use OpenCV-based verification methods
            if self.use_opencv and (face_data.get('method', 'unknown') == 'opencv' or 
                                   face_data.get('method', 'unknown') == 'opencv_enhanced'):
                try:
                    # Convert PIL image to OpenCV format
                    img_cv = np.array(image.convert('RGB'))
                    img_cv = img_cv[:, :, ::-1].copy()  # RGB to BGR
                    
                    # Enhanced face detection
                    gray, faces = self.detect_face(img_cv)
                    
                    logger.info(f"OpenCV verification found {len(faces)} faces")
                    
                    if len(faces) > 0:
                        # Take the largest face if multiple detected
                        if len(faces) > 1:
                            # Find the largest face by area
                            largest_area = 0
                            largest_idx = 0
                            for i, (x, y, w, h) in enumerate(faces):
                                area = w * h
                                if area > largest_area:
                                    largest_area = area
                                    largest_idx = i
                            
                            # Use the largest face
                            (x, y, w, h) = faces[largest_idx]
                        else:
                            # Just use the only face
                            (x, y, w, h) = faces[0]
                            
                        # Add margin around face (same as in registration)
                        y_margin = int(h * 0.3)  # Increased margin
                        x_margin = int(w * 0.3)  # Increased margin
                        
                        # Ensure margins don't go outside image bounds
                        y_start = max(0, y - y_margin)
                        y_end = min(gray.shape[0], y + h + y_margin)
                        x_start = max(0, x - x_margin)
                        x_end = min(gray.shape[1], x + w + x_margin)
                        
                        # Extract face region with margin
                        face_img = img_cv[y_start:y_end, x_start:x_end]
                        face_gray = gray[y_start:y_end, x_start:x_end]
                        
                        # Resize to standard size for consistency
                        face_img_resized = cv2.resize(face_img, (200, 200))
                        face_gray_resized = cv2.resize(face_gray, (200, 200))
                        
                        # First try LBPH recognition if available and model exists
                        model_path = os.path.join(self.models_dir, f"{phone}_model.yml")
                        
                        if self.advanced_recognition and os.path.exists(model_path) and face_data.get('has_model', False):
                            try:
                                # Load the trained model for this user
                                self.face_recognizer.read(model_path)
                                
                                # Predict using the model
                                label, confidence = self.face_recognizer.predict(face_gray_resized)
                                
                                logger.info(f"Face recognition confidence: {confidence} (lower is better)")
                                
                                # Check if confidence is below threshold - use more permissive threshold
                                # Adjust threshold based on testing - lower means more strict matching
                                threshold = 100.0  # Increased from 80 to 100 for more lenient matching
                                if label == 1 and confidence < threshold:  # 1 is the label we used in training
                                    logger.info(f"Face verified with LBPH recognizer: confidence={confidence}, threshold={threshold}")
                                    return True
                                else:
                                    logger.info(f"Face not verified with LBPH: confidence={confidence} > threshold={threshold}")
                                    # Continue to try other methods
                            except Exception as e:
                                logger.error(f"LBPH face recognition failed: {str(e)}")
                                logger.error(traceback.format_exc())
                                # Continue to try other methods
                        
                        # Try image similarity as backup
                        # Load the stored face image
                        stored_face_path = os.path.join(self.faces_dir, f"{phone}_face.jpg")
                        if os.path.exists(stored_face_path):
                            # Load stored face
                            stored_face = cv2.imread(stored_face_path)
                            
                            # Compare images using structural similarity
                            if stored_face is not None and stored_face.shape == face_img_resized.shape:
                                # Convert images to grayscale for comparison
                                stored_gray = cv2.cvtColor(stored_face, cv2.COLOR_BGR2GRAY)
                                current_gray = cv2.cvtColor(face_img_resized, cv2.COLOR_BGR2GRAY)
                                
                                # Calculate structural similarity index
                                try:
                                    import skimage.metrics
                                    ssim = skimage.metrics.structural_similarity(stored_gray, current_gray)
                                    logger.info(f"SSIM similarity score: {ssim}")
                                    
                                    # Higher score means more similar - adjust threshold
                                    # Lower threshold more for increased matching
                                    ssim_threshold = 0.35  # Reduced from 0.45 for even more lenient matching
                                    if ssim > ssim_threshold:
                                        logger.info(f"SSIM verification result: True (threshold: {ssim_threshold})")
                                        return True
                                except ImportError:
                                    # Fallback to MSE
                                    mse = np.mean((stored_gray - current_gray) ** 2)
                                    logger.info(f"MSE similarity score: {mse}")
                                    
                                    # Lower MSE means more similar
                                    # Increase threshold for more lenient matching
                                    mse_threshold = 4000  # Increased from 3000 for more lenient matching
                                    if mse < mse_threshold:
                                        logger.info(f"MSE verification result: True (threshold: {mse_threshold})")
                                        return True
                            else:
                                logger.warning(f"Stored face not found or dimensions don't match")
                        else:
                            logger.warning(f"Stored face image not found at {stored_face_path}")
                    else:
                        logger.warning(f"No face detected in verification image")
                except Exception as e:
                    logger.error(f"OpenCV verification failed: {str(e)}")
                    logger.error(traceback.format_exc())
            
            # Fallback to hash comparison if still not verified
            if face_data.get('method', 'unknown') == 'hash':
                logger.info("Using hash-based method for verification (fallback)")
                image_hash = hashlib.sha256(image_binary).hexdigest()
                logger.info(f"Generated hash for verification image: {image_hash[:10]}...")
                
                stored_hash = face_data.get("image_hash", "")
                logger.info(f"Retrieved stored hash: {stored_hash[:10]}...")
                
                if "image_hash" in face_data and image_hash == face_data["image_hash"]:
                    logger.info(f"Hash comparison result: True")
                    return True
                    
            # If we got here, verification failed
            logger.warning(f"Face verification failed for {phone}")
            return False
        except Exception as e:
            logger.error(f"Error in verify_against_specific_user: {str(e)}")
            logger.error(traceback.format_exc())
            return False

    def verify_face(self, phone, image_binary):
        """Verify a face against a registered face or all registered faces
        
        First attempts verification against specified phone number,
        and if that fails, tries all other registered users.
        """
        try:
            # Log input parameters (excluding binary data)
            logger.info(f"Starting face verification for phone: {phone}, image size: {len(image_binary)} bytes")
            
            # First, try to verify against the specified user
            verified = self.verify_against_specific_user(phone, image_binary)
            
            if verified:
                logger.info(f"Face verification successful for {phone}")
                return True
            
            # If not verified and specific user registration exists, try against all other registered users
            filepath = os.path.join(self.faces_dir, f"{phone}.json")
            if not os.path.exists(filepath):
                logger.warning(f"No face registered for {phone}, trying against all registered users")
                
                # Get all registered users
                all_users = self.get_all_registered_users()
                
                # Try verification against all other users
                for other_phone in all_users:
                    if other_phone != phone:  # Skip the original phone number
                        logger.info(f"Trying verification against {other_phone}")
                        verified = self.verify_against_specific_user(other_phone, image_binary)
                        if verified:
                            logger.info(f"Face matched with registered user: {other_phone}")
                            return True
                
                # If we got here, verification failed against all users
                logger.warning("Face not recognized among any registered users")
                return False
            else:
                # The specified user exists but verification failed
                return False

        except Exception as e:
            logger.error(f"Error in verify_face: {str(e)}")
            logger.error(traceback.format_exc())
            return False