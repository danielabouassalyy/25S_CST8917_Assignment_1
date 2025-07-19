import logging
import azure.functions as func
import azure.durable_functions as df

def main(myblob: func.InputStream, starter: str):
    client = df.DurableOrchestrationClient(starter)
    instance_id = client.start_new("OrchestratorFunction", None, myblob.name)
    logging.info(f"✅ Started orchestration for blob '{myblob.name}', instance ID = {instance_id}")
