from ninja import NinjaAPI
import dijk.models as mo

api = NinjaAPI()


@api.get("/hello")
def hello(request):
    return "Hello world"


@api.get("/zones")
def getZones(request):
    return [
        {"value": str(z), "label": str(z)}
        for z in mo.Zone.objects.all()
    ]
