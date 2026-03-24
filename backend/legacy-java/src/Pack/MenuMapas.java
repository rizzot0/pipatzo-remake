package Pack;

import javax.swing.JDialog;
import javax.swing.JPanel;
import javax.swing.JButton;
import javax.swing.BoxLayout;
import java.awt.event.ActionListener;
import java.awt.event.ActionEvent;
import java.io.File;
import java.util.LinkedList;
import java.util.Map;
import javax.swing.*;

public class MenuMapas extends JDialog {
    private JPanel panel;
    private static final String[] ciudades = {
        "Coquimbo",
        "La Serena",
        "Santiago",
        "Antofagasta",
        "Punta Arenas"
    };

    public MenuMapas() {
        setTitle("Seleccionar un mapa");
        setSize(300, 200);
        setDefaultCloseOperation(JDialog.DISPOSE_ON_CLOSE);

        panel = new JPanel();
        panel.setLayout(new BoxLayout(panel, BoxLayout.Y_AXIS));

        for (String ciudad : ciudades) {
            addButton(ciudad);
        }

        add(panel);
    }

    private void addButton(String ciudad) {
        JButton button = new JButton(ciudad);
        button.addActionListener(new ActionListener() {
            public void actionPerformed(ActionEvent e) {
                // Carga el mapa correspondiente cuando se hace clic en un botón
                cargarMapa(ciudad);
            }
        });
        panel.add(button);
    }

    private void cargarMapa(String cityName) {
        // Construir los nombres de los archivos de nodos y bordes
        String nodesFileName = cityName.toLowerCase() + "_nodes.xml";
        String edgesFileName = cityName.toLowerCase() + "_edges.xml";

        // Lógica para cargar el mapa desde los archivos nodes y edges
        //LinkedList<Nodo> nodos = leerNodoXML(new File(nodesFileName));
        //LinkedList<Edge> edges = leerEdgeXML(new File(edgesFileName));

        // Crear un mapa de nodos
        //Map<String, Nodo> nodosMap = crearDiccionarioNodos(nodos);

        // Configurar la ventana para mostrar el mapa
        //Ventana panel = new Ventana(nodos, edges);
        JScrollPane scrollPane = new JScrollPane(panel);

        // Configurar las barras de desplazamiento
        scrollPane.setHorizontalScrollBarPolicy(JScrollPane.HORIZONTAL_SCROLLBAR_ALWAYS);
        scrollPane.setVerticalScrollBarPolicy(JScrollPane.VERTICAL_SCROLLBAR_ALWAYS);

        // Crear el JFrame y configurarlo
        JFrame frame = new JFrame("Mapa de " + cityName);
        frame.setDefaultCloseOperation(JFrame.DISPOSE_ON_CLOSE);
        frame.setSize(800, 600);
        frame.getContentPane().add(scrollPane);

        // Hacer visible el JFrame
        frame.setVisible(true);
    }

//    private LinkedList<Nodo> leerNodoXML(File file) {
//        // Implementa la lógica para leer los nodos desde el archivo XML
//        // Retorna una lista de nodos
//        // Similar a tu método leerNodoXML en la clase Menú
//    }
//
//    private LinkedList<Edge> leerEdgeXML(File file) {
//        // Implementa la lógica para leer los bordes desde el archivo XML
//        // Retorna una lista de bordes
//        // Similar a tu método leerEdgeXML en la clase Menú
//    }
//
//    private Map<String, Nodo> crearDiccionarioNodos(List<Nodo> nodos) {
//        // Implementa la lógica para crear un diccionario de nodos
//        // Similar a tu método crearDiccionarioNodos en la clase Menú
//    }
}
