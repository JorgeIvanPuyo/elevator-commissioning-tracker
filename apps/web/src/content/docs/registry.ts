export type TechnicalDocument = {
  slug: string;
  title: string;
  description: string;
  category: string;
  relatedTestTypeCode: string;
};

export const technicalDocuments: TechnicalDocument[] = [
  {
    slug: "load-test",
    title: "Prueba de carga",
    description: "Calibración A61E/A62E y verificación de sobrepeso al 110%.",
    category: "Carga",
    relatedTestTypeCode: "LOAD_TEST",
  },
  {
    slug: "fine-leveling",
    title: "Nivelación fina",
    description: "DL/UL, A65E, A66E y medición piso a piso.",
    category: "Nivelación",
    relatedTestTypeCode: "FINE_LEVELING",
  },
  {
    slug: "load-compensation",
    title: "Compensación de carga",
    description: "Proceso A67E y parámetros de compensación 266, 240-245.",
    category: "Compensación",
    relatedTestTypeCode: "LOAD_COMPENSATION",
  },
  {
    slug: "parameter-adjustment",
    title: "Ajuste de parámetros",
    description: "Parámetros manuales, bias por zona y warnings min/max.",
    category: "Parámetros",
    relatedTestTypeCode: "PARAMETER_ADJUSTMENT",
  },
  {
    slug: "floor-measurement",
    title: "Medición piso a piso",
    description: "Origen, destino, tipo de viaje, dirección, landing/final y renivelación.",
    category: "Medición",
    relatedTestTypeCode: "FLOOR_MEASUREMENT",
  },
];

export function getTechnicalDocument(slug: string): TechnicalDocument | undefined {
  return technicalDocuments.find((document) => document.slug === slug);
}
