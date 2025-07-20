import azure.durable_functions as df

def main(context: df.DurableOrchestrationContext):
    image_name = context.get_input()
    metadata   = yield context.call_activity("ExtractMetadata", image_name)
    yield       context.call_activity("StoreMetadata", metadata)
    return      metadata
