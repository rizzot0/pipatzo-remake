package Pack;

import javax.swing.*;
import java.awt.*;
import java.awt.event.*;
import java.awt.geom.AffineTransform;
import java.util.ArrayList;
import java.util.List;
import java.text.DecimalFormat;

public class Ventana extends JPanel {
	//Inicializacion de listas a utilizar
    private List<Nodo> nodos;
    private List<Edge> bordes;
    //Utilizadas cuando se haga un reinicio de mapa
    private List<Nodo> nodosOriginales;
    private List<Edge> bordesOriginales;
    //Lista para la seleccion de nodos al hacer click en la pantalla
    private List<Nodo> nodosSeleccionados = new ArrayList<>();
    private double zoom = 1.0;
    //Movimiento del Mouse
    private int prevMouseX;
    private int prevMouseY;
    private int panX;
    private int panY;
    private boolean panning = false;
    private double xv, yv, xv2, yv2;
    
    
    // Area visible ventana
    private Rectangle visibleArea = new Rectangle();

    public Ventana(List<Nodo> nodos, List<Edge> bordes, double xv, double yv, double xv2, double yv2) {
        this.nodos = nodos;
        this.bordes = bordes;
        this.xv = xv;
        this.xv2 = xv2;
        this.yv = yv;
        this.yv2 = yv2;
        this.nodosOriginales = new ArrayList<>(nodos);
        this.bordesOriginales = new ArrayList<>(bordes);
        
        addMouseListener(new MouseAdapter() {
            @Override
            public void mousePressed(MouseEvent e) {
            	
            	if (SwingUtilities.isLeftMouseButton(e)) {
                    prevMouseX = e.getX();
                    prevMouseY = e.getY();
                    panning = true;
                    DecimalFormat f = new DecimalFormat("#.####");

                    // Convertir las coordenadas del mouse al espacio original (sin zoom)
                    double mouseX = (e.getX() - panX) / zoom;
                    double mouseY = (e.getY() - panY) / zoom;

                    /*Seleccion de dos nodos y mostrar sus datos*/
                    Nodo nodoClic = encontrarNodoMasCercano(mouseX, mouseY);

                    if (nodoClic != null) {
                        // Si ya hay 2 nodos seleccionados, borrar la lista
                        if (nodosSeleccionados.size() == 2) {
                            for (Nodo n : nodosSeleccionados) {
                                n.setDesmarcar();
                            }
                            nodosSeleccionados.clear();
                        }
                        nodosSeleccionados.add(nodoClic);
                        nodoClic.setMarcado(panning);

                        // Mostrar los datos de los nodos seleccionados
                        if (nodosSeleccionados.size() == 2) {
                            System.out.println("Nodos seleccionados:\n");
                            for (Nodo nodo : nodosSeleccionados) {
                                System.out.println(nodo.toString());
                            }

                            // Calcular y mostrar la distancia entre los nodos seleccionados
                            double distancia = calcularDistanciaEntreNodos(nodosSeleccionados.get(0),
                                    nodosSeleccionados.get(1));
                            String dist = f.format(distancia);
                            System.out.println("Distancia entre los nodos seleccionados: " + distancia);
                            JOptionPane.showMessageDialog(null,
                                    "Distancia entre los nodos seleccionados: \n" + dist + " Km\nNodo 1: "
                                            + nodosSeleccionados.get(0).getOsmid() + " \nX: "
                                            + f.format(nodosSeleccionados.get(0).getX()) + "\nY: "
                                            + f.format(nodosSeleccionados.get(0).getY()) + "\nNodo 2: "
                                            + nodosSeleccionados.get(1).getOsmid() + " \nX: "
                                            + f.format(nodosSeleccionados.get(1).getX()) + "\nY: "
                                            + f.format(nodosSeleccionados.get(1).getY()));
                        }
                    
                    }
                    repaint();
            	}
            }

            @Override
            public void mouseReleased(MouseEvent e) {
                if (SwingUtilities.isLeftMouseButton(e)) {
                    panning = false;
                }
            }
        });

        /*Desplazamiento de la ventana*/
        addMouseMotionListener(new MouseAdapter() {
            @Override
            public void mouseDragged(MouseEvent e) {
                if (panning) {
                    int deltaX = e.getX() - prevMouseX;
                    int deltaY = e.getY() - prevMouseY;

                    panX += deltaX;
                    panY += deltaY;

                    prevMouseX = e.getX();
                    prevMouseY = e.getY();

                    repaint();
                }
            }
        });

        //Aplicar zoom al mover la rueda del mouse, utilizando MouseWheelListener
        addMouseWheelListener(new MouseAdapter() {
            @Override
            public void mouseWheelMoved(MouseWheelEvent e) {
                int notches = e.getWheelRotation();
                double zoomFactor = Math.pow(1.1, notches);

                // Obtener las coordenadas del punto en el que se encuentra el puntero del mouse
                Point mousePoint = e.getPoint();

                // Calcular el desplazamiento antes del zoom
                double preZoomX = (mousePoint.getX() - panX) / zoom;
                double preZoomY = (mousePoint.getY() - panY) / zoom;

                // Aplicar el zoom
                setZoom(getZoom() * zoomFactor);

                // Calcular el desplazamiento después del zoom
                double postZoomX = (mousePoint.getX() - panX) / zoom;
                double postZoomY = (mousePoint.getY() - panY) / zoom;

                // Ajustar el desplazamiento para mantener el punto bajo el puntero del mouse
                panX += (preZoomX - postZoomX) * zoom;
                panY += (preZoomY - postZoomY) * zoom;

                repaint();
            }
        });
        
        // Crear un botón para reiniciar el mapa
        JButton reiniciarBoton = new JButton("Reiniciar Mapa");
        reiniciarBoton.addActionListener(new ActionListener() {
            public void actionPerformed(ActionEvent e) {
                reiniciarMapa();
            }
        });

        //Crear un JPanel para contener el botón de reinicio
        JPanel botonPanel = new JPanel();
        botonPanel.add(reiniciarBoton);

        setLayout(new BorderLayout());
        add(botonPanel, BorderLayout.NORTH); 
       
    }

    /*Dibujo del mapa*/
    
    @Override
    protected void paintComponent(Graphics g) {
        super.paintComponent(g);

        Graphics2D g2d = (Graphics2D) g;

        // Establecer el área de recorte (clipping) basada en la ventana
        g2d.setClip(0, 0, getWidth(), getHeight());

        g2d.setTransform(new AffineTransform());

        g2d.translate(panX, panY);
        g2d.scale(zoom, zoom);

        for (Edge borde : bordes) {
            Nodo nodoFuente = borde.getNodoFuente();
            Nodo nodoDestino = borde.getNodoDestino();
            if (nodoFuente != null && nodoDestino != null) {
                int x1 = escalarCoordenada(nodoFuente.getX(), xv, xv2, 0, getWidth());
                int y1 = escalarCoordenada(nodoFuente.getY(), yv, yv2, 0, getHeight());
                int x2 = escalarCoordenada(nodoDestino.getX(), xv, xv2, 0, getWidth());
                int y2 = escalarCoordenada(nodoDestino.getY(), yv, yv2, 0, getHeight());

                // Aplicar el zoom a las coordenadas de los bordes
                x1 = (int) (x1 * zoom);
                y1 = (int) (y1 * zoom);
                x2 = (int) (x2 * zoom);
                y2 = (int) (y2 * zoom);

                if (bordeEsVisible(x1, y1, x2, y2)) {
                	if(borde.getName().contains("Ruta")) {
                		g2d.setColor(Color.red);
                		g2d.drawLine(x1, y1, x2, y2);
                		g2d.setColor(Color.red);	
                	}
                	
                	else if(borde.getName().contains("nan")) {
                		g2d.setColor(Color.magenta);
                		g2d.drawLine(x1, y1, x2, y2);
                		g2d.setColor(Color.magenta);	
                	} 
                	else {
                		g2d.setColor(Color.darkGray);
                		g2d.drawLine(x1, y1, x2, y2);
                		g2d.setColor(Color.darkGray);
                		}
                }
            }
        }
    
        for (Nodo nodo : nodos) {
            int x = escalarCoordenada(nodo.getX(), xv, xv2, 0, getWidth());
            int y = escalarCoordenada(nodo.getY(), yv, yv2, 0, getHeight());

            // Aplicar el zoom a las coordenadas del nodo
            x = (int) (x * zoom);
            y = (int) (y * zoom);

            if (nodoEsVisible(x, y, nodo)) {
                // Dibuja el nodo solo si es visible
                nodo.dibujar(g2d, getWidth(), getHeight(), zoom);
            }
        }
    }
    
    //Aplica un reinicio de mapa para volver a su estado inicial
    private void reiniciarMapa() {
        // Restaura los nodos y bordes a su estado original
    	for (Nodo n : nodosSeleccionados) {
            n.setDesmarcar();
        }
        nodosSeleccionados.clear();
        nodos.clear();
        nodos.addAll(nodosOriginales);
        bordes.clear();
        bordes.addAll(bordesOriginales);
        zoom = 1.0;
        panX = 0;
        panY = 0;
        repaint();
    }
    
    //Escala las coordenadas de los archivos analizados para que se muestren en la pantalla.
    private int escalarCoordenada(double valor, double rangoMinEntrada, double rangoMaxEntrada, int rangoMinSalida,
            int rangoMaxSalida) {
        return (int) (((valor - rangoMinEntrada) * (rangoMaxSalida - rangoMinSalida))
                / (rangoMaxEntrada - rangoMinEntrada) + rangoMinSalida);
    }

    

    // Método para actualizar el área visible en la ventana
    private void actualizarAreaVisible() {
        int width = getWidth();
        int height = getHeight();

        visibleArea = new Rectangle(
            0, 0,              
            (int)(width / zoom),
            (int)(height / zoom)
        );
    }

    // Método para verificar si un nodo es visible en la ventana
    private boolean nodoEsVisible(int x, int y, Nodo nodo) {
        // Verifica si las coordenadas del nodo están dentro del área visible
        int nodoWidth = (int) (nodo.NODO_ANCHO * zoom); // Ancho del nodo escalado
        int nodoHeight = (int) (nodo.NODO_ALTO * zoom); // Alto del nodo escalado

        // Coordenadas escaladas del nodo, considerando el desplazamiento
        int scaledX = x - panX;
        int scaledY = y - panY;

        // Verificar si el nodo está dentro del área visible
        return (scaledX >= -nodoWidth && scaledX <= getWidth() && scaledY >= -nodoHeight && scaledY <= getHeight());
    }
    
    // Método para verificar si un borde es visible en el área visible
    private boolean bordeEsVisible(int x1, int y1, int x2, int y2) {
        return visibleArea.intersectsLine(x1, y1, x2, y2);
    }
    
    //Encuentra el nodo mas cercanco al momento de hacer click en el mapa para seleccionarlo
    public Nodo encontrarNodoMasCercano(double mouseX, double mouseY) {
        Nodo nodoMasCercano = null;
        double distanciaMinima = Double.MAX_VALUE; // Inicializar con un valor grande

        for (Nodo nodo : nodos) {
            int x = escalarCoordenada(nodo.getX(), xv, xv2, 0, getWidth());
            int y = escalarCoordenada(nodo.getY(), yv, yv2, 0, getHeight());

            // Aplicar el zoom y el desplazamiento a las coordenadas del nodo
            double nodoX = (x - panX) / zoom;
            double nodoY = (y - panY) / zoom;

            // Calcular la distancia entre el nodo y el clic del ratón considerando el zoom actual
            double distanciaX = nodoX - mouseX;
            double distanciaY = nodoY - mouseY;
            double distanciaCuadrado = distanciaX * distanciaX + distanciaY * distanciaY;

            if (distanciaCuadrado < distanciaMinima) {
                distanciaMinima = distanciaCuadrado;
                nodoMasCercano = nodo;
            }
        }

        return nodoMasCercano;
    }

    //Al seleccionar los dos nodoos, calcula la distancia entre ambos
    private double calcularDistanciaEntreNodos(Nodo nodo1, Nodo nodo2) {
        double lat1 = nodo1.getX();
        double lon1 = nodo1.getY();
        double lat2 = nodo2.getX();
        double lon2 = nodo2.getY();
        double distancia = calcularDistancia(lat1, lon1, lat2, lon2);
        return distancia;
    }

    //Obteniendo los datos de los nodos seleccionados calcula su distancia a escala 1x1
    private double calcularDistancia(double lat1, double lon1, double lat2, double lon2) {
        double radioTierra = 6371.0;

        // Convertir las coordenadas de grados a radianes
        lat1 = Math.toRadians(lat1);
        lon1 = Math.toRadians(lon1);
        lat2 = Math.toRadians(lat2);
        lon2 = Math.toRadians(lon2);

        // Diferencias de latitud y longitud
        double dLat = lat2 - lat1;
        double dLon = lon2 - lon1;

        // Fórmula de Haversine
        double a = Math.pow(Math.sin(dLat / 2), 2) + Math.cos(lat1) * Math.cos(lat2) * Math.pow(Math.sin(dLon / 2), 2);
        double c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));

        // Calcular la distancia
        double distancia = radioTierra * c;

        return distancia;
    }
    
    public void setZoom(double zoom) {
        this.zoom = zoom;
        actualizarAreaVisible();
        repaint();
    }

    public double getZoom() {
        return zoom;
    }

}