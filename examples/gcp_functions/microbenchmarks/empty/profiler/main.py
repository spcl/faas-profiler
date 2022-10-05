import faas_profiler_python as fp

@fp.profile()
def empty(request):
   return "empty"

