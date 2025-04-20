import qrcode
import io
import base64
import logging

logger = logging.getLogger(__name__)

def generate_qr_code(data, box_size=10, border=4):
    """
    Generate QR code for given data
    
    Args:
        data (str): Data to encode in QR
        box_size (int, optional): Box size. Defaults to 10.
        border (int, optional): Border size. Defaults to 4.
        
    Returns:
        str: Base64 encoded QR code image
    """
    try:
        # Create QR code instance
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_H,
            box_size=box_size,
            border=border
        )
        
        # Add data
        qr.add_data(data)
        qr.make(fit=True)
        
        # Create an image
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Save to bytes buffer
        buffer = io.BytesIO()
        img.save(buffer)
        buffer.seek(0)
        
        # Convert to base64
        img_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
        
        return f"data:image/png;base64,{img_base64}"
    
    except Exception as e:
        logger.error(f"Error generating QR code: {str(e)}")
        return None

def decode_qr_code(qr_data):
    """
    Decode QR code data
    
    Args:
        qr_data (str): QR code data string
        
    Returns:
        dict: Decoded information
    """
    try:
        # For ticket QR codes (train|coach|seat|phone)
        if qr_data.count('|') == 3:
            train_number, coach, seat, phone = qr_data.split('|')
            return {
                'type': 'ticket',
                'train_number': train_number,
                'coach': coach,
                'seat': seat,
                'phone': phone
            }
        # For standing zone QR codes (train|coach|zone|phone)
        elif qr_data.count('|') == 3:
            train_number, coach, zone, phone = qr_data.split('|')
            return {
                'type': 'standing_zone',
                'train_number': train_number,
                'coach': coach,
                'zone': zone,
                'phone': phone
            }
        else:
            return {'type': 'unknown', 'data': qr_data}
    
    except Exception as e:
        logger.error(f"Error decoding QR data: {str(e)}")
        return {'type': 'error', 'message': str(e)}
