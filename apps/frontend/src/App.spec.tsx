import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";

// Componente simple para probar el entorno sin dependencias complejas del App real
const TestComponent = () => (
  <div>
    <h1>Voice2Machine GUI</h1>
    <p>Interfaz de control para el daemon</p>
  </div>
);

describe("Pruebas Básicas de Frontend (Smoke Tests)", () => {
  it("debería renderizar el componente de prueba correctamente", () => {
    render(<TestComponent />);

    // Verificación en español
    const titulo = screen.getByText("Voice2Machine GUI");
    expect(titulo).toBeInTheDocument();

    const descripcion = screen.getByText("Interfaz de control para el daemon");
    expect(descripcion).toBeInTheDocument();
  });

  it("debería ejecutar aserciones básicas de Vitest", () => {
    const suma = 2 + 2;
    expect(suma).toBe(4);
  });
});
