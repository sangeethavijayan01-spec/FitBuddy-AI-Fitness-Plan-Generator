class FitBuddyError(Exception):
    status_code=400
    def __init__(self,user_message,status_code=None):
        super().__init__(user_message); self.user_message=user_message
        if status_code is not None:self.status_code=status_code
class AuthError(FitBuddyError): status_code=401
class ForbiddenError(FitBuddyError): status_code=403
class PlanNotFoundError(FitBuddyError): status_code=404
class DatabaseOperationError(FitBuddyError): status_code=500
class AIConfigError(FitBuddyError): status_code=503
class AIRequestError(FitBuddyError): status_code=502
class AIResponseError(FitBuddyError): status_code=502
