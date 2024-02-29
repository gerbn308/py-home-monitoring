import math
import os

class Weather():
    appName = "Personal Home Automation Stuff"
    contact = os.environ["contact"] if "contact" in os.environ else "undefined@contact.fake"

    @staticmethod
    def c_to_f( deg ):
        """
        Converts Degrees Celsius to Degrees Fahrenheit
        """
        return round( ( deg * 9/5 ) + 32, 3 )

    @staticmethod
    def f_to_c( deg ):
        """
        Converts Degrees Fahrenheit to Degrees Celsius
        °C = (°F - 32) × 5/9
        """
        return round( ( deg - 32 ) * (5/9), 3 )

    @staticmethod
    def in_to_mm( inches ):
        return round( inches * 25.4, 3 )

    @staticmethod
    def mm_to_in( mm ):
        return round( mm / 25.4, 3 )

    @staticmethod
    def text_to_inches( text ):
        if 'tenth' in text:     return 0.1
        elif 'quarter' in text: return 0.25  # Possible flaw is inch and a quarter or three quarters
        elif 'half' in text:    return 0.5
        return None
