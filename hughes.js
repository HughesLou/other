//global bindings :
//codebase
//log
//CONNECT_LOCK

function connect() {
  log.info("connecting");
  CONNECT_LOCK.acquire();
  try {
    // TODO:
  } finally {
    CONNECT_LOCK.release();
  }
}

var services = {};

function executeFormula(formula) {
  var retry = false;
  var retryCount = 0;
  do {
    // TODO
    }
  } while(retry)
}
