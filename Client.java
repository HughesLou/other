package com.hughes;

import java.io.BufferedInputStream;
import java.io.ByteArrayInputStream;
import java.io.File;
import java.io.IOException;
import java.io.InputStream;
import java.lang.Thread.UncaughtExceptionHandler;
import java.net.URL;
import java.net.URLClassLoader;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardCopyOption;
import java.nio.file.StandardOpenOption;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.concurrent.Semaphore;
import java.util.concurrent.SynchronousQueue;
import java.util.concurrent.TimeUnit;
import java.util.zip.CRC32;
import java.util.zip.CheckedInputStream;

import javax.script.ScriptEngine;
import javax.script.ScriptEngineManager;
import javax.script.ScriptException;
import javax.xml.parsers.DocumentBuilderFactory;
import javax.xml.xpath.XPathConstants;
import javax.xml.xpath.XPathFactory;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.w3c.dom.Document;
import org.w3c.dom.Element;
import org.w3c.dom.NodeList;

import com.google.common.io.ByteStreams;
import com.sun.jersey.api.client.WebResource;

public class Client {
    
    private final static Logger log = LoggerFactory.getLogger(Client.class);

    private String downloadPath;//http://uklpaurzr31a.uk.standardchartered.com:15500/murex/download/sdk/sdk-data-dictionary-api.download
    
    private String codebase;
    
    private boolean changed;
    
    private File rootFolder;
    
    private ClassLoader murexClientClassLoader;
    
    private ClientRunScriptThread executionThread;
    
    public void afterPropertiesSet() throws Exception {
        
        if(codebase == null) {
            throw new RuntimeException("mandatory property 'codebase'");
        }
        if(rootFolder == null) {
            throw new RuntimeException("mandatory property 'rootFolder'");
        }
        if(downloadPath == null) {
            throw new RuntimeException("mandatory property 'downloadPath'");
        }
        if(executionThread == null) {
            executionThread = new ClientRunScriptThread();
            executionThread.setName("murexclient-" + downloadPath);
            executionThread.setDaemon(false);
            executionThread.setUncaughtExceptionHandler(new UncaughtExceptionHandler() {
                public void uncaughtException(Thread t, Throwable e) {
                    log.error("uncaught exception in thread {}, for murexclient {}, {}", t, codebase, downloadPath, e);
                }
            });
            executionThread.setClient(this);
            executionThread.setInitialScript(new String(ByteStreams.toByteArray(getClass().getResourceAsStream("murex.js"))));
        }
    }
    /**
     * create a separate classloader for murex jars and facade classes<br/>
     * It is synchronized per instance
     */
    public ClassLoader getMurexClientClassLoader() throws Exception {
        
        if(murexClientClassLoader != null) {
            return murexClientClassLoader;
        }
        
        refresh();
        File[] files = rootFolder.listFiles();
        List<URL> urls = new ArrayList<URL>();
        for(File f : files) {
            urls.add(f.toURI().toURL());
        }
        //this could lead to memory leak
        murexClientClassLoader = new URLClassLoader(urls.toArray(new URL[urls.size()]), null);
        return murexClientClassLoader;
    }
    
    public Object runScript(String script) throws Exception {
        return executionThread.runScript(script);
    }
    
    /**
     * use this lock when you try to establish murex connection. System.setProperty('codebase'...) should be in lock period
     */
    public final static Semaphore CONNECT_LOCK = new Semaphore(1); //allow only one murex client to do connecting at any time across entire VM
    
    /**
     * fetch latest jars from murex server
     */
    public void refresh() throws Exception {
        //1. download jar file map from murex server xxx.download
        //2. compare crc32 of local jar and in jar file map, if changed download and override
        //3. remove local jar that not in jar file map
        com.sun.jersey.api.client.Client client = com.sun.jersey.api.client.Client.create();
        WebResource root = client.resource(codebase);
        WebResource wr = client.resource(codebase + downloadPath + "?InternalVersion=2");
        String xml = wr.get(String.class);
        log.info("downloadPath content {}", xml);
        Document document = DocumentBuilderFactory.newInstance().newDocumentBuilder().parse(new ByteArrayInputStream(xml.getBytes()));
        NodeList nodes = (NodeList)XPathFactory.newInstance().newXPath().evaluate("//File", document, XPathConstants.NODESET);
        if(rootFolder.exists() == false) rootFolder.mkdir();
        Map<String, String> map = new HashMap<String, String>();
        for(int i = 0; i < nodes.getLength(); i++) {
            Element node = (Element) nodes.item(i);
            String path = node.getTextContent().trim();
            String fileName = path.substring(path.lastIndexOf("/") + 1);
            Path filePath = new File(rootFolder, fileName).toPath();
            if(filePath.toFile().exists()) {
                String checksum = crc32(filePath);
                if(checksum.equals(node.getAttribute("CheckSum2"))) {
                    map.put(fileName, checksum);
                    continue; //no change
                }
            }
            
            InputStream stream = root.path(path).get(InputStream.class);
            log.info("update {}", filePath);
            Files.copy(stream, filePath, StandardCopyOption.REPLACE_EXISTING);
            map.put(fileName, crc32(filePath));
            changed = true;
        }
        File[] files = rootFolder.listFiles();
        for(File f : files) {
            if(map.keySet().contains(f.getName()) == false) {
                log.info("delete {}", f.getPath());
                f.delete();
                changed = true;
            }
        }
        log.info("are jars changed since last run ?  {}", changed);
    }
    
    private String crc32(Path filePath) throws IOException {
        try(InputStream fin = Files.newInputStream(filePath, StandardOpenOption.READ);
            BufferedInputStream buf = new BufferedInputStream(fin);
            CheckedInputStream stream = new CheckedInputStream(buf, new CRC32());) {
            while(stream.read() != -1){}
            return String.valueOf(stream.getChecksum().getValue());
        }
    }

    public String getDownloadPath() {
        return downloadPath;
    }

    public void setDownloadPath(String downloadPath) {
        this.downloadPath = downloadPath;
    }

    public boolean isChanged() {
        return changed;
    }

    public void setChanged(boolean changed) {
        this.changed = changed;
    }

    public File getRootFolder() {
        return rootFolder;
    }

    public void setRootFolder(File rootFolder) {
        this.rootFolder = rootFolder;
    }

    public String getCodebase() {
        return codebase;
    }

    public void setCodebase(String codebase) {
        this.codebase = codebase;
    }

    public void setMurexClientClassLoader(ClassLoader murexClientClassLoader) {
        this.murexClientClassLoader = murexClientClassLoader;
    }
    public Thread getExecutionThread() {
        return executionThread;
    }
    
}

class ClientRunScriptThread extends Thread {
    
    private final static Logger log = LoggerFactory.getLogger(ClientRunScriptThread.class);
    
    private Client client;
    
    private String initialScript;
    
    private SynchronousQueue<String> input = new SynchronousQueue<String>(true);
    
    private SynchronousQueue<Object> output = new SynchronousQueue<Object>(true);
    
    public void run() {
        ScriptEngineManager sem = new ScriptEngineManager();
        ScriptEngine scriptEngine = sem.getEngineByName("js");
        scriptEngine.put("CONNECT_LOCK", Client.CONNECT_LOCK);
        scriptEngine.put("codebase", client.getCodebase());
        scriptEngine.put("log", log);
        try {
            System.out.println(initialScript);
            scriptEngine.eval(initialScript);
        } catch (ScriptException e1) {
            log.error("fail to run initial script", e1);
        }
        while(true) {
            String script = null;
            try {
                script = input.take();
            } catch (InterruptedException e) {
                log.warn("thread interrupted", e);
                break;
            }
            Object rtn = null;
            try {
                rtn = scriptEngine.eval(script);
            } catch(ScriptException e2) {
                log.error("script execution error for {}", script, e2);
            }
            try {
                output.put(rtn);
            } catch (InterruptedException e) {
                log.error("SERIOUS ERROR !!! thread interrupted, a call to runScript may block forever");
            }
        }
    }
    
    public Object runScript(String script) throws InterruptedException {
        if(State.NEW.equals(getState())) {
            start();
        }
        boolean offered = input.offer(script, 30, TimeUnit.SECONDS);
        if(offered == false) {
            throw new RuntimeException("fail to offer script for execution in 10 seconds " + script);
        }
        return output.take();
    }
    
    @Override
    public synchronized void start() {
        try {
            setContextClassLoader(client.getMurexClientClassLoader());
        } catch (Exception e) {
            throw new RuntimeException(e);
        }
        super.start();
    }
    
    public Client getClient() {
        return client;
    }
    
    public void setClient(Client client) {
        this.client = client;
    }
    
    public SynchronousQueue<String> getInput() {
        return input;
    }
    
    public void setInput(SynchronousQueue<String> input) {
        this.input = input;
    }
    
    public SynchronousQueue<Object> getOutput() {
        return output;
    }
    
    public void setOutput(SynchronousQueue<Object> output) {
        this.output = output;
    }

    public String getInitialScript() {
        return initialScript;
    }

    public void setInitialScript(String initialScript) {
        this.initialScript = initialScript;
    }
}

