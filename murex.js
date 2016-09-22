//global bindings :
//codebase
//log
//CONNECT_LOCK

function connect() {
  log.info("connecting");
  CONNECT_LOCK.acquire();
  try {
    java.lang.System.setProperty('murex.application.codebase', codebase);
    var ap = Packages.murex.shared.arguments.ArgumentsParser.create(['/MXJ_SITE_NAME:site1']);
    var conn = new Packages.murex.apps.middleware.client.home.connection.XmlLayerConnection(ap);
    var regsvc = new Packages.murex.sdk.middleware.v31.MurexServiceRegistryFactoryImpl();
    var registry = regsvc.newMurexServiceRegistryFromExistingConnection(conn);
    return registry;
  } finally {
    CONNECT_LOCK.release();
  }
}

var services = {};

function executeFormula(formula) {
  var retry = false;
  var retryCount = 0;
  do {
    if(!services.registry) {
      services.registry = connect();
      services.dd = new Packages.murex.sdk.datadictionary.v31.DataDictionaryServiceImpl(services.registry, true);
    }
    try {
      var matrix = services.dd.executeFormula(formula, new Packages.murex.sdk.datadictionary.SimpleFormulaParameters());
      return matrix.getColumn(0);
    } catch (ex) {
      retry = ex.getCause() instanceof Packages.murex.apps.middleware.client.core.server.connection.ClientConnectionException && retryCount < 10;
      retry && retryCount++;
      retry && log.error("retry {}th connect due to exception", ex);
      retry || log.error("unexpected exception ", ex);
      if(retry) {
        services.registry = null;
      }
    }
  } while(retry)
}
