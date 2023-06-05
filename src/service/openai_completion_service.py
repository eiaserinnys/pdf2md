from colorama import Fore, Style
from enum import Enum
from typing import Optional
from dataclasses import dataclass
from src.service.logger import logger
from src.config import global_config
import openai

# Set up OpenAI API configuration
openai.api_key = global_config.OPENAI_API_KEY

class CompletionResult(Enum):
    OK = 0
    TOO_LONG = 1
    INVALID_REQUEST = 2
    OTHER_ERROR = 3
    MODERATION_FLAGGED = 4
    MODERATION_BLOCKED = 5
    RATE_LIMITED = 6

@dataclass
class CompletionData:
    status: CompletionResult
    reply_text: Optional[str] = None
    status_text: Optional[str] = None
    prompt_tokens: Optional[int] = None
    completion_tokens: Optional[int] = None

class OpenAICompletionService:
    @staticmethod
    def system_message(str:str):
        return { "role": "system", "content": str }

    @staticmethod
    def user_message(str:str):
        return { "role": "user", "content": str }

    @staticmethod
    def assistant_message(str:str):
        return { "role": "assistant", "content": str }
    
    @staticmethod
    def dump_prompt(messages):
        for message in messages:
            if message["role"] == "user":
                print(
                    Fore.RED + '{:<10}'.format(message["role"]) +
                    Fore.LIGHTYELLOW_EX + message["content"])
            elif message["role"] == "assistant":
                print(
                    Fore.RED + '{:<10}'.format(message["role"]) +
                    Fore.YELLOW + message["content"])
            else: # system
                print(
                    Fore.RED + '{:<10}'.format(message["role"]) +
                    Fore.BLUE + message["content"])
        print(Style.RESET_ALL)

    @staticmethod
    def dump_response(response:CompletionData):
        print(Fore.RED + "RESPONSE(" + response.status.name + "):" + Fore.GREEN)
        if response.status_text != None:
            print("Status:" + response.status_text)
        if response.reply_text != None:
            print(response.reply_text)
        if response.prompt_tokens != None and response.completion_tokens != None:
            print(Fore.RED + f"Total({str(response.prompt_tokens + response.completion_tokens)}) = Prompt({str(response.prompt_tokens)}) + Completion({str(response.completion_tokens)})") 
        print(Style.RESET_ALL)
    
    @staticmethod
    async def async_request_chat_completion(
        model, 
        messages, 
        max_tokens=None, 
        temperature=None, 
        top_p=None, 
        stop=None, 
        stream=False,
        verbose_prompt=False, 
        verbose_response=False) -> CompletionData:

        if verbose_prompt:
            OpenAICompletionService.dump_prompt(messages)

        try:
            if stream:
                result = ""
                prompt_tokens = 0
                completion_tokens = 0

                if verbose_response:
                    print(Fore.RED + "RESPONSE: " + Fore.GREEN)

                async for chunk in await openai.ChatCompletion.acreate(
                    model=model,
                    messages=messages,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    top_p=top_p,
                    stop=stop,
                    stream=True,
                ):
                    content = chunk["choices"][0].get("delta", {}).get("content")

                    if content is not None:
                        result += content
                        if verbose_response:
                            print(content, end='')

                    if "usage" in chunk:
                        prompt_tokens += chunk["usage"]["prompt_tokens"]
                        completion_tokens += chunk["usage"]["completion_tokens"]

                if verbose_response:
                    print()

                return CompletionData(
                    status=CompletionResult.OK,
                    reply_text=result,
                    prompt_tokens=prompt_tokens,
                    completion_tokens=completion_tokens,
                )                
            else:
                completion = await openai.ChatCompletion.acreate(
                    model=model,
                    messages=messages,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    top_p=top_p,
                    stop=stop
                )

                response = CompletionData(
                    status=CompletionResult.OK, 
                    reply_text=completion.choices[0].message["content"], 
                    status_text=None,
                    prompt_tokens=completion.usage.prompt_tokens 
                        if hasattr(completion.usage, "prompt_tokens") else None,
                    completion_tokens=completion.usage.completion_tokens 
                        if hasattr(completion.usage, "completion_tokens") else None
                )

                if verbose_response:
                    OpenAICompletionService.dump_response(response)

                return response

        except openai.error.RateLimitError as e:
            logger.exception(e)
            return CompletionData(status=CompletionResult.RATE_LIMITED, status_text=str(e))

        except openai.error.InvalidRequestError as e:
            if "This model's maximum context length" in e.user_message:
                return CompletionData(status=CompletionResult.TOO_LONG, status_text=str(e))
            else:
                logger.exception(e)
                return CompletionData(status=CompletionResult.INVALID_REQUEST, status_text=str(e))

        except Exception as e:
            logger.exception(e)
            return CompletionData(status=CompletionResult.OTHER_ERROR, status_text=str(e))
        
        finally:
            if verbose_prompt or verbose_response:
                print(Style.RESET_ALL, '')

    @staticmethod
    def request_chat_completion(
        model, 
        messages, 
        max_tokens=None, 
        temperature=None, 
        top_p=None, 
        stop=None, 
        verbose_prompt=False, 
        verbose_response=False) -> CompletionData:

        if verbose_prompt:
            OpenAICompletionService.dump_prompt(messages)

        try:
            completion = openai.ChatCompletion.create(
                model=model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature,
                top_p=top_p,
                stop=stop
            )

            response = CompletionData(
                status=CompletionResult.OK, 
                reply_text=completion.choices[0].message["content"], 
                status_text=None,
                prompt_tokens=completion.usage.prompt_tokens 
                    if hasattr(completion.usage, "prompt_tokens") else None,
                completion_tokens=completion.usage.completion_tokens 
                    if hasattr(completion.usage, "completion_tokens") else None
            )

            if verbose_response:
                OpenAICompletionService.dump_response(response)

            return response

        except openai.error.RateLimitError as e:
            logger.exception(e)
            return CompletionData(status=CompletionResult.RATE_LIMITED, status_text=str(e))

        except openai.error.InvalidRequestError as e:
            if "This model's maximum context length" in e.user_message:
                return CompletionData(status=CompletionResult.TOO_LONG, status_text=str(e))
            else:
                logger.exception(e)
                return CompletionData(status=CompletionResult.INVALID_REQUEST, status_text=str(e))

        except Exception as e:
            logger.exception(e)
            return CompletionData(status=CompletionResult.OTHER_ERROR, status_text=str(e))
        
        finally:
            if verbose_prompt or verbose_response:
                print(Style.RESET_ALL, '')
