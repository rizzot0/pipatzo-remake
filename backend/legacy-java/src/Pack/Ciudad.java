package Pack;

    public class Ciudad
    {
        private String xmlNodes;
        private String xmlEdges;

        public Ciudad(String xmlNodes, String xmlEdges)
        {
            this.xmlNodes = xmlNodes;
            this.xmlEdges = xmlEdges;
        }

        public String getXmlNodes()
        {
            return xmlNodes;
        }

        public String getXmlEdges()
        {
            return xmlEdges;
        }
    }