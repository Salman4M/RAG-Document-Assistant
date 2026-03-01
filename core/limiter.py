from slowapi import Limiter
from fastapi import Request

#rate limiting based on user id
def get_user_id(request:Request)-> str:
    user = getattr(request.state, "user_id", None)
    if user:
        return str(user)
    return request.client.host

limiter = Limiter(key_func=get_user_id)