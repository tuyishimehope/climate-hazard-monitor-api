import aiohttp

class ApiClient:
    
    def __init__(self,):
        self.session = ""
        
    async def init_client(self):
        async with aiohttp.ClientSession() as session:
            self.session = session
            return session