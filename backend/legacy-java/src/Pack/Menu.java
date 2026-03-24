package Pack;

import java.awt.*;
import java.awt.event.ActionEvent;
import java.awt.event.ActionListener;
import java.io.File;
import java.io.IOException;
import java.util.HashMap;
import java.util.LinkedList;
import java.util.List;
import java.util.Map;
import java.util.*;
import javax.swing.*;
import javax.xml.parsers.DocumentBuilder;
import javax.xml.parsers.DocumentBuilderFactory;

import org.w3c.dom.Document;
import org.w3c.dom.Element;
import org.w3c.dom.NodeList;

public class Menu extends JFrame {
	//Inicializar List para el relacionamiento de los archivos nodes.xml y edges.xml
	static Map<String, Nodo> nodosMap = new HashMap<>();
	private LinkedList<Nodo> Nodos = new LinkedList<>();
	private LinkedList<Edge> Edges = new LinkedList<>();
	private LinkedList<Nodo> NodosOriginales = new LinkedList<>();
	private LinkedList<Edge> EdgesOriginales = new LinkedList<>();
	//Variables para calcular las coordenadas de la clase ventana para mostrar el mapa dibujado
	private double xv = 0, xv2 = 0, yv = 0, yv2 = 0;

	private JPanel contentPane;

	//Inicializacion del JFrame
	public static void main(String[] args) {
		EventQueue.invokeLater(new Runnable() {
			public void run() {
				try {
					Menu frame = new Menu();
					frame.setLocationRelativeTo(null);
				} catch (Exception e) {
					e.printStackTrace();
				}
			}
		});
	}

	/*Menu : inicializa las pestañas con sus correspondientes paneles
	 * Panel 1 : Encargado de la carga de archivos locales
	 * Panel 2 : Encargado de la carga de archivos remotos
	 * */
	public Menu() {
		setDefaultCloseOperation(JFrame.EXIT_ON_CLOSE);
		setBounds(100, 100, 652, 393);

		JTabbedPane tabbedPane = new JTabbedPane();
		
		 // Panel 1: Carga Directa
        JPanel panelCargaDirecta = panelCargaDirectaJPanel();
        tabbedPane.addTab("Carga Local", null, panelCargaDirecta, "Realizar acciones locales");
        
        // Panel 2: Carga Remota
        JPanel panelCargaRemota = createPanelCargaRemota();
        tabbedPane.addTab("Carga Remota", null, panelCargaRemota, "Realizar acciones con archivos remotos");

        //Creacion JFrame
		JFrame frame = new JFrame("Lectura de mapas");
		frame.setDefaultCloseOperation(JFrame.EXIT_ON_CLOSE);
		frame.setSize(800, 600);

		frame.getContentPane().add(tabbedPane);

		frame.setVisible(true);
	}
	
	//Inicializa las funciones para la carga de archivos locales
	private JPanel panelCargaDirectaJPanel() {
		 JPanel panel = new JPanel();
	        panel.setLayout(null);

	        JButton LeerNodo = BotonNodos();
	        JButton LeerEdges = BotonEdges();
	        JButton MostrarMapa = BotonMostrarMapa();

	        panel.add(LeerNodo);
	        panel.add(LeerEdges);
	        panel.add(MostrarMapa);

	        return panel;
	}
	
	//Inicializa el boton de la carga de nodos en el panel de carga directa
	private JButton BotonNodos() {
	        JButton button = new JButton("Leer Nodos");
	        button.setFont(new Font("Arial Black", Font.PLAIN, 14));
	        button.setBounds(234, 200, 144, 21);
	        button.addActionListener(new ActionListener() {
				public void actionPerformed(ActionEvent e) {
					File f = new File("C:\\Users\\maxm2\\OneDrive\\Escritorio\\Proyecto_Mapav2");
					JFileChooser fileChooser = new JFileChooser();
					fileChooser.setCurrentDirectory(f);
					int returnValue = fileChooser.showOpenDialog(null);

					if (returnValue == JFileChooser.APPROVE_OPTION) {
						File selectedFile = fileChooser.getSelectedFile();
						leerNodoXML(selectedFile);
					}
				}
			});
	        return button;
	    }

	//Inicializa el boton de la carga de edges en el panel de carga directa
	private JButton BotonEdges() {
	        JButton button = new JButton("Leer Edges");
	        button.setFont(new Font("Arial Black", Font.PLAIN, 14));
	        button.setBounds(234, 241, 144, 21);
	        button.addActionListener(new ActionListener() {
				public void actionPerformed(ActionEvent e) {
					File f = new File("C:\\Users\\maxm2\\OneDrive\\Escritorio\\Proyecto_Mapav2");
					JFileChooser fileChooser = new JFileChooser();
					fileChooser.setCurrentDirectory(f);
					int returnValue = fileChooser.showOpenDialog(null);

					if (returnValue == JFileChooser.APPROVE_OPTION) {
						File selectedFile = fileChooser.getSelectedFile();
						leerEdgeXML(selectedFile);
					}
				}		
			});
	        return button;
	    }

	//Inicializa el boton de la muestra de mapas en el panel de carga directa
	private JButton BotonMostrarMapa() {
	        JButton button = new JButton("Mostrar Mapa");
	        button.setFont(new Font("Arial Black", Font.PLAIN, 14));
	        button.setBounds(234, 282, 144, 21);
	        button.addActionListener(new ActionListener() {
				public void actionPerformed(ActionEvent e) {
					Map<String, Nodo> nodosMap = crearDiccionarioNodos(Nodos);
					for (Edge Edge : Edges) {
						Nodo nodoFuente = nodosMap.get(Edge.getU());
						Nodo nodoDestino = nodosMap.get(Edge.getV());
						Edge.setNodoFuente(nodoFuente);
						Edge.setNodoDestino(nodoDestino);
					}

					// Crear el JFrame y configurarlo
					JFrame frame = new JFrame("Dibujar Nodos y Bordes desde XML");
					frame.setDefaultCloseOperation(JFrame.EXIT_ON_CLOSE);
					frame.setSize(800, 600);
					frame.setVisible(true);
				}
			});
	        return button;
	    }

	//Inicializa el panel de carga de archivos remota
	private JPanel createPanelCargaRemota() {
	        JPanel panel = new JPanel();
	        panel.setLayout(null);

	        JButton cargarArchivosRemotos = createCargarArchivosRemotosButton();
	        panel.add(cargarArchivosRemotos);

	        return panel;
	    }
	    
	//Boton para el cargado de archivos remotos, llama a la funcion cargarArchivosRemotos
	private JButton createCargarArchivosRemotosButton() {
	        JButton button = new JButton("Cargar Archivos Remotos");
	        button.setFont(new Font("Arial Black", Font.PLAIN, 14));
	        button.setBounds(234, 200, 250, 30);
	        button.addActionListener(e -> cargarArchivosRemotos());
	        return button;
	    }
	    
	//Utiliza las funciones de la clase CiudadesProvider para la carga de archivos remota
	private void cargarArchivosRemotos() {
	        try {
	            CiudadesProvider ciudadesProvider = CiudadesProvider.instance();

	            List<String> ciudades = ciudadesProvider.list();
	            StringBuilder message = new StringBuilder("Lista de ciudades disponibles:\n");
	            for (int i = 0; i < ciudades.size(); i++) {
	                message.append((i + 1)).append(". ").append(ciudades.get(i)).append("\n");
	            }

	            String input = JOptionPane.showInputDialog(null, message.toString(),
	                    "Seleccione un mapa ingresando su número", JOptionPane.PLAIN_MESSAGE);

	            if (input != null) {
	                int selectedMapIndex = Integer.parseInt(input);
	                if (selectedMapIndex >= 1 && selectedMapIndex <= ciudades.size()) {
	                    String selectedMap = ciudades.get(selectedMapIndex - 1);
	                    System.out.println("Mapa seleccionado: " + selectedMap);

	                    Ciudad c = ciudadesProvider.ciudad(selectedMap);
	                    String archivoNodos = c.getXmlNodes();
	                    String archivoEdges = c.getXmlEdges();

	                    ciudadesProvider.cargarArchivosRemotos(archivoNodos, archivoEdges);
	                    System.out.println("Carga de archivos remotos completada");
	                } else {
	                    System.out.println("Número de mapa no válido. Saliendo...");
	                }
	            }
	        } catch (IOException ex) {
	            ex.printStackTrace();
	        }
	    }
	    
	//Procesa el archivo nodes.xml de manera local,retorna la lista de nodos
	private LinkedList<Nodo> leerNodoXML(File selectedFile) {
		try {
			DocumentBuilderFactory factory = DocumentBuilderFactory.newInstance();
			DocumentBuilder builder = factory.newDocumentBuilder();
			Document doc = builder.parse(selectedFile);

			NodeList nodeList = doc.getElementsByTagName("row");
			for (int i = 0; i < nodeList.getLength(); i++) {
				Element elemento = (Element) nodeList.item(i);
				double x = Double.parseDouble(elemento.getElementsByTagName("x").item(0).getTextContent());
				double y = Double.parseDouble(elemento.getElementsByTagName("y").item(0).getTextContent());
				String osmid = elemento.getElementsByTagName("osmid").item(0).getTextContent();
				Nodo nodo = new Nodo(x, y, osmid);
				Nodos.add(nodo);
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

			for (Nodo nodo : Nodos) {
				nodo.setXv(xv);
				nodo.setXv2(xv2);
				nodo.setYv(yv);
				nodo.setYv2(yv2);
			}
			System.out.println("X: " + xv + " X2: " + xv2);
			System.out.println("Y: " + yv + " Y2: " + yv2);
			NodosOriginales.addAll(Nodos);
		} catch (Exception e) {
			e.printStackTrace();
		}

		return Nodos;
	}
	
	//Procesa el archivo edges.xml de manera local,retorna la lista de edges
	private LinkedList<Edge> leerEdgeXML(File selectedFile) {
		try {
			DocumentBuilderFactory factory = DocumentBuilderFactory.newInstance();
			DocumentBuilder builder = factory.newDocumentBuilder();
			Document doc = builder.parse(selectedFile);

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
				Edges.add(edge);
				
			}
			EdgesOriginales.addAll(Edges);
		} catch (Exception e) {
			e.printStackTrace();
		}

		return Edges;
	}
	
	//Ingresa los nodos procesados a un hashMap para su relacionamiento con los edges en la funcion mostrarMapa
	private static Map<String, Nodo> crearDiccionarioNodos(List<Nodo> nodos) {
		Map<String, Nodo> nodosMap = new HashMap<>();
		for (Nodo nodo : nodos) {
			nodosMap.put(nodo.getOsmid(), nodo);
		}
		return nodosMap;
	}
}
