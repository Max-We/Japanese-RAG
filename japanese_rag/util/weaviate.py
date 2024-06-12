import weaviate


def get_weaviate_client(url, key):
    try:
        return weaviate.Client(
            url=url,
            auth_client_secret=weaviate.AuthApiKey(api_key=key)
        )
    except:
        return None
