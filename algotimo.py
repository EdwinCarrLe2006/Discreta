from ortools.linear_solver import pywraplp

def main():
    solver = pywraplp.Solver.CreateSolver("SCIP")
    if not solver:
        raise Exception("No se pudo crear el solver.")

    # Datos mejor estructurados
    clientes = ['C1', 'C2', 'C3', 'C4', 'C5']
    satelites = ['S1', 'S2']
    hubs = ['H1', 'H2']
    
    # Datos de ubicación (coordenadas simuladas)
    ubicaciones = {
        'H1': {'nombre': 'Centro de Lima', 'direccion': 'Av. Abancay 123', 'coords': (-12.0464, -77.0428)},
        'H2': {'nombre': 'San Isidro', 'direccion': 'Av. Javier Prado Este 456', 'coords': (-12.0972, -77.0338)},
        'S1': {'coords': (-12.0650, -77.0450)},
        'S2': {'coords': (-12.0950, -77.0500)},
        'C1': {'nombre': 'Cliente A', 'direccion': 'Av. Arequipa 1000, Lince', 'coords': (-12.0821, -77.0345)},
        'C2': {'nombre': 'Cliente B', 'direccion': 'Av. Brasil 2000, Magdalena', 'coords': (-12.0900, -77.0700)},
        'C3': {'nombre': 'Cliente C', 'direccion': 'Av. La Marina 3000, San Miguel', 'coords': (-12.0800, -77.1000)},
        'C4': {'nombre': 'Cliente D', 'direccion': 'Av. Benavides 4000, Surco', 'coords': (-12.1300, -77.0100)},
        'C5': {'nombre': 'Cliente E', 'direccion': 'Av. Universitaria 5000, San Juan', 'coords': (-12.1400, -77.0000)}
    }

    demanda = {'C1': 10, 'C2': 15, 'C3': 8, 'C4': 12, 'C5': 7}
    capacidad_vehiculo = 30

    costos = {
        'hub': {'H1': 50, 'H2': 60},
        'satelite': {'S1': 10, 'S2': 12},
        'cliente_satelite': {
            ('C1', 'S1'): 1.5, ('C2', 'S1'): 2.0,
            ('C3', 'S2'): 1.2, ('C4', 'S2'): 2.3,
            ('C5', 'S1'): 1.8
        },
        'satelite_hub': {
            ('S1', 'H1'): 3.0, ('S1', 'H2'): 4.0,
            ('S2', 'H1'): 2.5, ('S2', 'H2'): 2.8
        },
        'entre_hubs': {('H1', 'H2'): 5.0, ('H2', 'H1'): 5.0}
    }

    # Variables
    Y = {h: solver.BoolVar(f'Y[{h}]') for h in hubs}
    X_cs = {(c, s): solver.BoolVar(f'X[{c},{s}]') for (c, s) in costos['cliente_satelite']}
    Z_sh = {(s, h): solver.BoolVar(f'Z[{s},{h}]') for (s, h) in costos['satelite_hub']}
    X_hh = {(h1, h2): solver.BoolVar(f'X_hh[{h1},{h2}]') for (h1, h2) in costos['entre_hubs']}

    # Función objetivo
    solver.Minimize(
        sum(costos['hub'][h] * Y[h] for h in hubs) +
        sum(costos['satelite'][s] * sum(X_cs[c, s] for c in clientes if (c, s) in X_cs) for s in satelites) +
        sum(costos['cliente_satelite'][c, s] * X_cs[c, s] for (c, s) in X_cs) +
        sum(costos['satelite_hub'][s, h] * Z_sh[s, h] for (s, h) in Z_sh) +
        sum(costos['entre_hubs'][h1, h2] * X_hh[h1, h2] for (h1, h2) in X_hh)
    )

    # Restricciones
    for c in clientes:
        solver.Add(sum(X_cs[c, s] for s in satelites if (c, s) in X_cs) == 1)

    for s in satelites:
        solver.Add(sum(Z_sh[s, h] for h in hubs if (s, h) in Z_sh) >= 1)

    for (s, h) in Z_sh:
        solver.Add(Z_sh[s, h] <= Y[h])

    # Resolver
    status = solver.Solve()

    # Generar reporte detallado
    if status == pywraplp.Solver.OPTIMAL:
        print("\n" + "="*50)
        print("REPORTE DE RUTAS ÓPTIMAS DE DISTRIBUCIÓN")
        print("="*50 + "\n")
        
        # Hubs activos
        hubs_activos = [h for h in hubs if Y[h].solution_value() > 0.5]
        print(f"Hubs activos: {', '.join(hubs_activos)}")
        
        # Procesar asignaciones satélite-hub
        asignaciones_sh = {}
        for (s, h) in Z_sh:
            if Z_sh[s, h].solution_value() > 0.5:
                asignaciones_sh[s] = h
                print(f"\nSatélite {s} asignado al hub {h} ({ubicaciones[h]['nombre']})")
                print(f"  Distancia: {costos['satelite_hub'][(s, h)]} km")
                print(f"  Costo de transporte: ${costos['satelite_hub'][(s, h)]:.2f}")
        
        # Procesar rutas por satélite
        for s in satelites:
            clientes_asignados = [c for (c, s2) in X_cs if s2 == s and X_cs[(c, s2)].solution_value() > 0.5]
            if not clientes_asignados:
                continue
                
            demanda_total = sum(demanda[c] for c in clientes_asignados)
            hub_asociado = asignaciones_sh[s]
            
            print(f"\nRUTA PARA SATÉLITE {s} (conectado a {hub_asociado}):")
            print(f"Clientes asignados: {', '.join(clientes_asignados)}")
            print(f"Demanda total: {demanda_total} unidades")
            print(f"Capacidad del vehículo: {capacidad_vehiculo} unidades")
            
            if demanda_total > capacidad_vehiculo:
                print("¡ADVERTENCIA: Demanda excede capacidad del vehículo!")
                print("Solución recomendada: Dividir en 2 viajes o ajustar capacidad")
            
            print("\nDetalle de entregas:")
            for c in clientes_asignados:
                distancia = costos['cliente_satelite'][(c, s)]
                print(f"- {c}: {ubicaciones[c]['nombre']}")
                print(f"  Dirección: {ubicaciones[c]['direccion']}")
                print(f"  Demanda: {demanda[c]} unidades")
                print(f"  Distancia desde satélite: {distancia} km")
                print(f"  Costo de entrega: ${distancia:.2f}")
            
            costo_ruta = sum(costos['cliente_satelite'][(c, s)] for c in clientes_asignados)
            print(f"\nCosto total de la ruta: ${costo_ruta:.2f}")
        
        # Conexiones entre hubs
        conexiones_hubs = [(h1, h2) for (h1, h2) in X_hh if X_hh[(h1, h2)].solution_value() > 0.5]
        if conexiones_hubs:
            print("\nConexiones directas entre hubs:")
            for (h1, h2) in conexiones_hubs:
                print(f"{h1} -> {h2}: {costos['entre_hubs'][(h1, h2)]} km (Costo: ${costos['entre_hubs'][(h1, h2)]:.2f})")
        else:
            print("\nNo hay conexiones directas entre hubs en esta solución")
        
        print("\n" + "="*50)
        print(f"COSTO TOTAL DEL SISTEMA: ${solver.Objective().Value():.2f}")
        print("="*50)
        
    else:
        print("No se encontró solución óptima.")

if __name__ == "__main__":
    main()
