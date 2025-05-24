from datetime import datetime, timezone
import logging
import os
import traceback

class Logger:
    def __init__(self):
        self.base_log_dir = 'logs'
        if not os.path.exists(self.base_log_dir):
            os.makedirs(self.base_log_dir)

    def _setup_logger(self, logger_name: str, log_file: str) -> logging.Logger:
        logger = logging.getLogger(logger_name)
        
        if not logger.handlers:
            file_handler = logging.FileHandler(log_file)
            formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
            logger.setLevel(logging.ERROR)
        
        return logger

    def log_user_error(self, user_email: str, error: Exception, function_name: str = None):
        """Log errors related to user functionality (auth, profile, etc)"""
        user_dir = os.path.join(self.base_log_dir, user_email.replace('@', '_at_'))
        if not os.path.exists(user_dir):
            os.makedirs(user_dir)

        log_file = os.path.join(user_dir, 'user_errors.log')
        logger = self._setup_logger(f"user_{user_email}", log_file)

        stack_trace = ''.join(traceback.format_tb(error.__traceback__))
        error_message = f"""
User Error Details
------------------------
User Email: {user_email}
Error Type: {type(error).__name__}
Error Message: {str(error)}
Function: {function_name if function_name else 'Unknown'}
Stack Trace:
{stack_trace}
------------------------
"""
        logger.error(error_message)

    def log_session_error(self, session_id: str, error: Exception, function_name: str = None):
        """Log errors related to chat/session functionality"""
        session_dir = os.path.join(self.base_log_dir, 'sessions')
        if not os.path.exists(session_dir):
            os.makedirs(session_dir)

        log_file = os.path.join(session_dir, f"{session_id}.log")
        logger = self._setup_logger(f"session_{session_id}", log_file)

        stack_trace = ''.join(traceback.format_tb(error.__traceback__))
        error_message = f"""
Session Error Details
------------------------
Session ID: {session_id}
Error Type: {type(error).__name__}
Error Message: {str(error)}
Function: {function_name if function_name else 'Unknown'}
Stack Trace:
{stack_trace}
------------------------
"""
        logger.error(error_message)