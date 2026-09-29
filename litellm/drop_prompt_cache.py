from litellm.integrations.custom_logger import CustomLogger
import litellm

class DropPromptCache(CustomLogger):
    async def async_pre_call_hook(self, user_api_key_dict, cache, data, call_type):
        data.pop("prompt_cache", None)
        if isinstance(data.get("extra_body"), dict):
            data["extra_body"].pop("prompt_cache", None)
        return data

    def pre_call_hook(self, user_api_key_dict, cache, data, call_type):
        data.pop("prompt_cache", None)
        if isinstance(data.get("extra_body"), dict):
            data["extra_body"].pop("prompt_cache", None)
        return data

proxy_handler_instance = DropPromptCache()
