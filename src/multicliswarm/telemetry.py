from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource

def init_telemetry(enable_console: bool = False, otlp_endpoint: str = None):
    """
    Initializes OpenTelemetry tracing.
    If otlp_endpoint is provided, sends traces to a backend like Phoenix or Jaeger.
    """
    resource = Resource.create({"service.name": "MultiCliSwarm"})
    provider = TracerProvider(resource=resource)
    
    if enable_console:
        provider.add_span_processor(BatchSpanProcessor(ConsoleSpanExporter()))
        
    if otlp_endpoint:
        # e.g., "http://localhost:4318/v1/traces" or Arize Phoenix endpoint
        otlp_exporter = OTLPSpanExporter(endpoint=otlp_endpoint)
        provider.add_span_processor(BatchSpanProcessor(otlp_exporter))
        
    trace.set_tracer_provider(provider)

def get_tracer():
    return trace.get_tracer("multicliswarm")
