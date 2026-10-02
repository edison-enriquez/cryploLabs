# Padding Oracle Lab — listo para Codespaces

Folder `padding-oracle/` portable: funciona en local (Docker Desktop) y en GitHub Codespaces.
El atacante es el propio codespace. Solo se levanta el oráculo.

## Estructura

```
padding-oracle/
  docker-compose.yml  # solo oraculo, publica 5000 (L1) y 6000 (L2)
  task1.sh
  manual_attack_ES.py
  attack_l1.py
  attack_l1_p1.py
  attack_l2.py
../.devcontainer/devcontainer.json  # Docker-in-Docker + Python + forward 5000/6000
```

## 1. Abrir en Codespaces

1. Ve a https://github.com/edison-enriquez/cryploLabs
2. `Code` > `Codespaces` > `Create codespace on main` (2 cores basta).
3. Espera a `postCreateCommand` (instala openssl, docker, python).

## 2. Iniciar oráculo

```bash
cd padding-oracle
docker compose up -d
docker ps
# prueba rapida:
nc -vz 127.0.0.1 5000
nc -vz 127.0.0.1 6000
python3 -c "import socket;print(socket.create_connection(('127.0.0.1',5000),timeout=5).recv(4096).decode()[:96])"
```

No uses `10.9.0.80` en Codespaces. Los scripts ya usan `ORACLE_HOST=127.0.0.1` por defecto.
Solo si usas la red docker original (con kali) usa `ORACLE_HOST=10.9.0.80`.

## 3. Practica paso a paso

```bash
cd padding-oracle

# Task 1 - padding
bash task1.sh

# Task 2 - Nivel 1 manual/automatico (puerto 5000)
python3 manual_attack_ES.py
python3 attack_l1.py
python3 attack_l1_p1.py   # opcional, deriva P1

# Task 3 - Nivel 2 automatizado (puerto 6000, una sola conexion)
python3 attack_l2.py
```

## 4. Apagar

```bash
docker compose down
```

## Notas

- Cada conexion nueva a L2 (6000) genera clave/IV nuevos. Los scripts mantienen una sola conexion, no los cortes.
- L1 (5000) es determinista: IV+C1+C2 fijos.
- Si `docker compose` falla con `permission denied`, reabre el codespace (devcontainer ya da docker-in-docker).
