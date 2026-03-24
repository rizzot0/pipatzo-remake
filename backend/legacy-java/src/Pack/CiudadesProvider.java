package Pack;

import java.io.BufferedReader;
import java.io.IOException;
import java.io.InputStreamReader;
import java.net.HttpURLConnection;
import java.net.URL;
import java.net.URLConnection;
import java.util.List;
import java.util.zip.GZIPInputStream;

import org.json.JSONArray;
import org.json.JSONObject;
import org.w3c.dom.Document;
import org.w3c.dom.NodeList;

import java.util.*;
import java.io.*;
import javax.swing.*;
import java.awt.*;
import javax.xml.parsers.*;
import javax.xml.parsers.DocumentBuilderFactory;
import org.w3c.dom.Element;
import org.xml.sax.InputSource;



/**
 * Esta clase se encarga de listar y descargar archivos de datos NODE y EDGE
 * para ciudades. El origen de los datos es un servidor "en la nube".
 * 
 * Para ver cómo se usa esta clase, busque el "main" que está al final de 
 * este archivo.
 * 
 * Nótese: para que esta clase funcione, debe descargar el archivo jar
 * https://search.maven.org/remotecontent?filepath=org/json/json/20231013/json-20231013.jar
 * 
 * y agregarlo a las "biblotecas referenciadas" en su proyecto.
 * 
 * @see https://github.com/stleary/JSON-java
 */
public class CiudadesProvider
{
    static Map<String, Nodo> nodosMap = new HashMap<>();
	private static LinkedList<Nodo> NodosOriginales = new LinkedList<>();
	private static LinkedList<Edge> EdgesOriginales = new LinkedList<>();
	private static double xv = 0, xv2 = 0, yv = 0, yv2 = 0;
	
    private CiudadesProvider()
    {

    }

    private static CiudadesProvider theInstance = null;

    public static CiudadesProvider instance()
    {
        if (theInstance == null) {
            theInstance = new CiudadesProvider();
        }
        return theInstance;
    }

    private String getURLContents(String enlace) throws IOException
    {
        URL url = new URL(enlace);
        URLConnection connection = url.openConnection();

        BufferedReader reader = new BufferedReader(new InputStreamReader(connection.getInputStream()));
        StringBuilder content = new StringBuilder();
        String line;

        while ((line = reader.readLine()) != null) {
            content.append(line).append("\n");
        }

        reader.close();

        String urlString = content.toString();
        return urlString;
    }
    private String getURLContentsZIP(String enlace) throws IOException
    {
        System.out.println("Downloading " + enlace);
        
        URL url = new URL(enlace);
        GZIPInputStream gzipInputStream = new GZIPInputStream(url.openStream());
        BufferedReader reader = new BufferedReader(new InputStreamReader(gzipInputStream, "UTF-8"));

        String line;
        StringBuilder content = new StringBuilder();
        while ((line = reader.readLine()) != null) {
            content.append(line);
        }
        reader.close();
        
        return content.toString();
    }

    public Ciudad ciudad(String nombre) throws IOException
    {
    	xv = 0;
    	xv2 = 0;
    	yv = 0;
    	yv2 = 0;
        URL url = new URL("https://losvilos.ucn.cl/eross/ciudades/get.php?d=" + nombre);
        HttpURLConnection connection = (HttpURLConnection) url.openConnection();
        connection.setRequestMethod("GET");

        BufferedReader reader = new BufferedReader(new InputStreamReader(connection.getInputStream()));
        StringBuilder response = new StringBuilder();
        String line;

        while ((line = reader.readLine()) != null) {
            response.append(line);
        }

        reader.close();
        connection.disconnect();

        JSONObject json = new JSONObject(response.toString());
        String nodes = json.getString("nodes");
        String edges = json.getString("edges");

        return new Ciudad(getURLContentsZIP(nodes), getURLContentsZIP(edges));
    }

    public List<String> list() throws IOException
    {
        URL url = new URL("https://losvilos.ucn.cl/eross/ciudades/list.php");
        HttpURLConnection connection = (HttpURLConnection) url.openConnection();
        connection.setRequestMethod("GET");

        BufferedReader reader = new BufferedReader(new InputStreamReader(connection.getInputStream()));
        StringBuilder response = new StringBuilder();
        String line;

        while ((line = reader.readLine()) != null) {
            response.append(line);
        }

        reader.close();
        connection.disconnect();

        JSONArray json = new JSONArray(response.toString());
        ArrayList<String> result = new ArrayList<>();

        for (Object o : json) {
            result.add(o.toString());
        }
        return result;
    }
    
    

    private static LinkedList<Nodo> leerNodoXML(String xmlText) {
        LinkedList<Nodo> nodos = new LinkedList<>();

        try {
            DocumentBuilderFactory factory = DocumentBuilderFactory.newInstance();
            DocumentBuilder builder = factory.newDocumentBuilder();
            Document doc = builder.parse(new InputSource(new StringReader(xmlText)));

            NodeList nodeList = doc.getElementsByTagName("row");
            for (int i = 0; i < nodeList.getLength(); i++) {
                Element elemento = (Element) nodeList.item(i);
                double x = Double.parseDouble(elemento.getElementsByTagName("x").item(0).getTextContent());
                double y = Double.parseDouble(elemento.getElementsByTagName("y").item(0).getTextContent());
                String osmid = elemento.getElementsByTagName("osmid").item(0).getTextContent();
                Nodo nodo = new Nodo(x, y, osmid);

                // Asocia las coordenadas xv, xv2, yv, yv2 a cada nodo
                nodo.setXv(xv);
                nodo.setXv2(xv2);
                nodo.setYv(yv);
                nodo.setYv2(yv2);

                nodos.add(nodo);
                nodosMap.put(osmid, nodo);
                // Actualiza las coordenadas xv, xv2, yv, yv2 según sea necesario
                if (xv2 == 0) {
                    xv2 = x;
                } else {
                    if (xv2 < x) {
                        xv2 = x;
                    }
                }
                if (xv > x) {
                    xv = x;
                }
                if (yv2 == 0) {
                    yv2 = y;
                } else {
                    if (yv2 < y) {
                        yv2 = y;
                    }
                }
                if (yv > y) {
                    yv = y;
                }
            }
            // Asocia las coordenadas xv, xv2, yv, yv2 a todos los nodos después de leerlos
            for (Nodo nodo : nodos) {
                nodo.setXv(xv);
                nodo.setXv2(xv2);
                nodo.setYv(yv);
                nodo.setYv2(yv2);
            }

            NodosOriginales.addAll(nodos);
        } catch (Exception e) {
            e.printStackTrace();
        }

        return nodos;
    }

    private static LinkedList<Edge> leerEdgeXML(String xmlText) {
        LinkedList<Edge> edges = new LinkedList<>();

        try {
            DocumentBuilderFactory factory = DocumentBuilderFactory.newInstance();
            DocumentBuilder builder = factory.newDocumentBuilder();
            Document doc = builder.parse(new InputSource(new StringReader(xmlText)));

            NodeList nodeList = doc.getElementsByTagName("edge");
            for (int i = 0; i < nodeList.getLength(); i++) {
                Element elemento = (Element) nodeList.item(i);
                String u = elemento.getElementsByTagName("u").item(0).getTextContent();
                String v = elemento.getElementsByTagName("v").item(0).getTextContent();
                int k = Integer.parseInt(elemento.getElementsByTagName("k").item(0).getTextContent());
                String osmid = elemento.getElementsByTagName("osmid").item(0).getTextContent();
                String name = elemento.getElementsByTagName("name").item(0).getTextContent();

                // Busca y asocia los nodos usando el mapa
                Nodo nodoFuente = nodosMap.get(u);
                Nodo nodoDestino = nodosMap.get(v);
                Edge edge = new Edge(u, v, k, osmid, name, nodoFuente, nodoDestino);
                edges.add(edge);
                
            }
            EdgesOriginales.addAll(edges);
        } catch (Exception e) {
            e.printStackTrace();
        }

        return edges;
    }

    private static Map<String, Nodo> crearDiccionarioNodos(List<Nodo> nodos, List<Edge> edges) {
		Map<String, Nodo> nodosMap = new HashMap<>();
		for (Nodo nodo : nodos) {
			nodosMap.put(nodo.getOsmid(), nodo);
		}
		for (Edge Edge : edges) {
			Nodo nodoFuente = nodosMap.get(Edge.getU());
			Nodo nodoDestino = nodosMap.get(Edge.getV());
			Edge.setNodoFuente(nodoFuente);
			Edge.setNodoDestino(nodoDestino);
		}
		return nodosMap;
	}  
    
    public void cargarArchivosRemotos(String archivoNodos, String archivoEdges) {
        try {
            LinkedList<Nodo> nodos = leerNodoXML(archivoNodos);
            LinkedList<Edge> edges = leerEdgeXML(archivoEdges);

            nodosMap = crearDiccionarioNodos(nodos, edges);

            // Crear una instancia de la clase Ventana
            Ventana panel = new Ventana(NodosOriginales, EdgesOriginales, xv, yv, xv2, yv2);

            // Crear un JScrollPane que contenga el panel Ventana
            JScrollPane scrollPane = new JScrollPane(panel);

            // Configurar el comportamiento de las barras de desplazamiento
            scrollPane.setHorizontalScrollBarPolicy(JScrollPane.HORIZONTAL_SCROLLBAR_ALWAYS);
            scrollPane.setVerticalScrollBarPolicy(JScrollPane.VERTICAL_SCROLLBAR_ALWAYS);

            // Crear el JFrame y configurarlo
            JFrame frame = new JFrame("Dibujar Nodos y Bordes desde XML");
            frame.setDefaultCloseOperation(JFrame.EXIT_ON_CLOSE);
            frame.setSize(800, 600);

            // Agregar el JScrollPane al contenido del JFrame
            frame.getContentPane().add(scrollPane);

            // Hacer visible el JFrame
            frame.setVisible(true);

        } catch (Exception e) {
            e.printStackTrace();
        }
    }
    
    public static void main(String[] args) {
        System.out.println("Testing----------------");

        CiudadesProvider p = CiudadesProvider.instance();
        String last = "";

        try {
            // Muestra la lista de ciudades disponibles
            System.out.println("Lista de ciudades disponibles:");
            for (String ciudad : p.list()) {
                System.out.println(ciudad);
                last = ciudad;
            }

            // Solicita al usuario que elija un mapa
            System.out.print("Seleccione un mapa ingresando su nombre: ");
            Scanner scanner = new Scanner(System.in);
            String selectedMap = scanner.nextLine();

            // Muestra el detalle del mapa seleccionado
            System.out.println("\nDetalle del mapa seleccionado:");
            Ciudad ciudad = p.ciudad(selectedMap);

            System.out.println("XML EDGES tiene tamaño " + ciudad.getXmlEdges().length());
            System.out.println("XML NODES tiene tamaño " + ciudad.getXmlNodes().length());

        } catch (IOException e) {
            e.printStackTrace();
        }
    }
}