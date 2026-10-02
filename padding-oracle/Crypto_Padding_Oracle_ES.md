# Laboratorio de Ataque Padding Oracle — Traducción al español

**Fuente original:** `Crypto_Padding_Oracle.pdf` — SEED Labs, Copyright © 2021 Wenliang Du.
**Licencia:** Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International.
**Página oficial:** https://seedsecuritylabs.org/Labs_20.04/Crypto/Crypto_Padding_Oracle/
**Traducción:** español (fiel al original, solo con fines académicos).

---

## 1. Descripción general

El objetivo de aprendizaje de este laboratorio es que los estudiantes obtengan experiencia práctica con un ataque interesante a sistemas criptográficos. Algunos sistemas, al descifrar un texto cifrado dado, verifican si el relleno (*padding*) es válido o no, y lanzan un error si el relleno es inválido. Este comportamiento en apariencia inofensivo permite un tipo de ataque llamado **ataque de oráculo de relleno (*padding oracle attack*)**. El ataque fue publicado originalmente en 2002 por Serge Vaudenay, y muchos sistemas conocidos resultaron vulnerables a este ataque, incluyendo Ruby on Rails, ASP.NET y OpenSSL.

En este laboratorio, se proporcionan a los estudiantes dos servidores oráculo ejecutándose dentro de un contenedor. Cada oráculo tiene un mensaje secreto oculto en su interior, y da a conocer el texto cifrado y el IV, pero no el texto plano ni la clave de cifrado. Usted puede enviar un texto cifrado (y el IV) al oráculo; este descifrará el texto cifrado usando la clave de cifrado, y le dirá si el relleno es válido o no. Su trabajo es usar la respuesta del oráculo para averiguar el contenido del mensaje secreto. Este laboratorio cubre los siguientes temas:

- Cifrado de clave secreta
- Modos de cifrado y rellenos
- Ataque de oráculo de relleno

**Lecturas.** La cobertura detallada del cifrado de clave secreta se puede encontrar en lo siguiente, pero el ataque de oráculo de relleno no está cubierto en la edición actual (ediciones futuras incluirán este ataque). Los estudiantes pueden encontrar tutoriales sobre este ataque en recursos en línea, como Wikipedia.

- Capítulo 21 del libro SEED, *Computer & Internet Security: A Hands-on Approach*, 2ª edición, por Wenliang Du. Ver detalles en https://www.handsonsecurity.net.

**Lectura previa recomendada (10 min).** Ejercicio gratuito de PentesterLab: https://pentesterlab.com/exercises/padding_oracle (<1h, nivel medio). Lea las secciones *Cipher Block Chaining*, *Padding*, *Padding Oracle* y *The theory*: su derivación `I15 = 0x01 ^ E'7` es la misma matemática de este laboratorio (`D2[pos] = CC1[pos] ⊕ K`). Fíjese en su conclusión (el cifrado sin autenticación permite descifrar y re-cifrar a gusto) y en su consejo de *manual exploitation*: escribir su propia herramienta antes de automatizar.

**Verificación con PadBuster.** PadBuster (https://github.com/GDSSecurity/PadBuster, Perl) automatiza este mismo ataque sobre aplicaciones HTTP. No se conecta directamente al oráculo TCP de este laboratorio; úselo en el ejercicio de PentesterLab para contrastar que entiende el comportamiento del oráculo:

```bash
git clone https://github.com/GDSSecurity/PadBuster && cd PadBuster
# Descifrar la cookie (bloque de 8 bytes en ese ejercicio):
perl padbuster.pl http://<IP-del-lab> "<cookie>" 8 -cookies "auth=<cookie>"
# Re-cifrar un mensaje a su elección:
perl padbuster.pl http://<IP-del-lab> "<cookie>" 8 -cookies "auth=<cookie>" -plaintext "user=admin"
```

Nota: el informe se califica sobre su propio código contra el oráculo SEED, no sobre salidas de PadBuster.

**Entorno de laboratorio.** Este laboratorio ha sido probado en la VM SEED Ubuntu 20.04. Puede descargar una imagen preconstruida desde el sitio web de SEED, y ejecutar la VM SEED en su propio computador. Sin embargo, la mayoría de los laboratorios SEED pueden realizarse en la nube, y puede seguir nuestras instrucciones para crear una VM SEED en la nube.

## 2. Entorno de laboratorio

En este laboratorio, usamos un contenedor para ejecutar el oráculo de relleno.

**Configuración del contenedor y comandos.** Por favor descargue el archivo `Labsetup.zip` a su VM desde el sitio web del laboratorio, descomprímalo, entre a la carpeta `Labsetup`, y use el archivo `docker-compose.yml` para configurar el entorno del laboratorio. Una explicación detallada del contenido de este archivo y de todos los Dockerfile involucrados se puede encontrar en el manual de usuario, que está enlazado en el sitio web de este laboratorio. Si es la primera vez que configura un entorno de laboratorio SEED usando contenedores, es muy importante que lea el manual de usuario.

A continuación, listamos algunos de los comandos de uso común relacionados con Docker y Compose. Dado que vamos a usar estos comandos con mucha frecuencia, hemos creado alias para ellos en el archivo `.bashrc` (en nuestra VM SEED Ubuntu 20.04 proporcionada).

```bash
$ docker-compose build # Construir las imágenes de los contenedores
$ docker-compose up    # Iniciar los contenedores
$ docker-compose down  # Apagar los contenedores

# Alias para los comandos Compose anteriores
$ dcbuild  # Alias de: docker-compose build
$ dcup     # Alias de: docker-compose up
$ dcdown   # Alias de: docker-compose down
```

Todos los contenedores se ejecutarán en segundo plano. Para ejecutar comandos en un contenedor, a menudo necesitamos obtener un shell en ese contenedor. Primero necesitamos usar el comando `docker ps` para averiguar el ID del contenedor, y luego usar `docker exec` para iniciar un shell en ese contenedor. Hemos creado alias para ellos en el archivo `.bashrc`.

```bash
$ dockps     # Alias de: docker ps --format "{{.ID}} {{.Names}}"
$ docksh <id> # Alias de: docker exec -it <id> /bin/bash

# El siguiente ejemplo muestra cómo obtener un shell dentro de hostC
$ dockps
b1004832e275 hostA-10.9.0.5
0af4ea7a3e2e hostB-10.9.0.6
9652715c8e0a hostC-10.9.0.7
$ docksh 96
root@9652715c8e0a:/#

# Nota: Si un comando docker requiere un ID de contenedor, no necesita
# escribir la cadena completa del ID. Escribir los primeros caracteres será
# suficiente, siempre que sean únicos entre todos los contenedores.
```

Si encuentra problemas al configurar el entorno del laboratorio, por favor lea la sección “Common Problems” del manual para posibles soluciones.

## 3. Tarea 1: Familiarizarse con el relleno

Para algunos cifrados por bloques, cuando el tamaño de un texto plano no es múltiplo del tamaño de bloque, puede requerirse relleno. El esquema de relleno PKCS#5 es ampliamente usado por muchos cifrados por bloques (ver Capítulo 21.4 del libro SEED para detalles). Sin embargo, PKCS#5 solo está definido para tamaños de bloque de 8 bytes. Esto resulta problemático para cifrados por bloques que tienen tamaños de bloque mayores a 8 bytes, como AES. Para solucionar este problema, se inventó el esquema de relleno PKCS#7. Realizaremos los siguientes experimentos para entender cómo funciona este tipo de relleno.

Podemos usar el comando `echo -n` para crear un archivo. El siguiente ejemplo crea un archivo `P` con longitud 5 (sin la opción `-n`, la longitud será 6, porque `echo` añadirá un carácter de nueva línea):

```bash
$ echo -n "12345" > P
```

Usamos `openssl enc -aes-128-cbc -e` para cifrar este archivo usando AES de 128 bits con modo CBC. Para ver qué se añade al relleno durante el cifrado, descifraremos el texto cifrado usando `openssl enc -aes-128-cbc -d`. Desafortunadamente, el descifrado por defecto eliminará automáticamente el relleno, haciendo imposible que veamos el relleno. Sin embargo, el comando tiene una opción llamada `-nopad`, que deshabilita el relleno, es decir, durante el descifrado, el comando no eliminará los datos acolchados. Por lo tanto, al observar los datos descifrados, podemos ver qué datos se usaron en el relleno.

```bash
$ openssl enc -aes-128-cbc -e -in P -out C
$ openssl enc -aes-128-cbc -d -nopad -in C -out P_new
```

Debe notarse que los datos de relleno pueden no ser imprimibles, por lo que necesita usar una herramienta hexadecimal para mostrar el contenido. El siguiente ejemplo muestra cómo mostrar un archivo en formato hexadecimal:

```bash
$ xxd P_new
00000000: 3132 3334 350b 0b0b 0b0b 0b0b 0b0b 0b0b  12345...........
```

Su trabajo es crear tres archivos, que contengan 5 bytes, 10 bytes y 16 bytes, respectivamente. Usando el método anterior, por favor averigüe qué rellenos se añaden a los tres archivos.

Al descifrar el archivo de 16 bytes, ¿por qué vemos un bloque completo de relleno? ¿Por qué es esto necesario?

## 4. Tarea 2: Ataque de oráculo de relleno (Nivel 1)

Algunos sistemas, al descifrar un texto cifrado dado, verifican si el relleno es válido o no, y lanzan un error si el relleno es inválido. Este comportamiento en apariencia inofensivo permite un tipo de ataque llamado ataque de oráculo de relleno. El ataque fue publicado originalmente en 2002 por Serge Vaudenay, y muchos sistemas conocidos fueron encontrados vulnerables a este tipo de ataques, incluyendo Ruby on Rails, ASP.NET y OpenSSL.

### 4.1 Configuración del oráculo

En esta tarea, proporcionamos un oráculo de relleno alojado en el puerto 5000. El oráculo tiene un mensaje secreto en su interior, e imprime el texto cifrado de este mensaje secreto. El algoritmo y modo de cifrado usado es AES-CBC, y la clave de cifrado es K, desconocida para otros. Puede interactuar con el oráculo usando `nc 10.9.0.80 5000`. Verá los siguientes datos hexadecimales proporcionados por el oráculo. Los primeros 16 bytes son el IV, y el resto es el texto cifrado. Por la longitud, puede ver que el texto cifrado tiene 32 bytes, es decir, 2 bloques, pero la longitud real del texto plano es desconocida debido al relleno.

```bash
$ nc 10.9.0.80 5000
01020304050607080102030405060708a9b2554b094411...
```

El oráculo acepta entradas de usted. El formato de la entrada es el mismo que el mensaje anterior: 16 bytes del IV, concatenados con el texto cifrado. El oráculo descifrará el texto cifrado usando su propia clave secreta K y el IV proporcionado por usted. No le dirá el texto plano, pero sí le dice si el relleno es válido o no. Su tarea es usar la información proporcionada por el oráculo para averiguar el contenido real del mensaje secreto. Por simplicidad, solo necesita averiguar un bloque del mensaje secreto.

Para fines de depuración, proporcionamos el mensaje secreto a continuación (está en el código fuente del oráculo).

```c
static std::array<unsigned char, 29> PLAIN_TEXT = {
  0x11, 0x22, 0x33, 0x44, 0x55, 0x66, 0x77, 0x88,
  0x11, 0x22, 0x33, 0x44, 0x55, 0x66, 0x77, 0x88,
  0x11, 0x22, 0x33, 0x44, 0x55, 0x66, 0x77, 0x88,
  0xaa, 0xbb, 0xcc, 0xdd, 0xee
};
```

El mensaje secreto se proporciona solo para fines de depuración, y no puede asumir que conoce este mensaje. Necesita usar el ataque de oráculo de relleno para derivar este mensaje; necesita mostrar sus pasos.

### 4.2 Derivar el texto plano manualmente

El objetivo de esta tarea es averiguar el texto plano del mensaje secreto. Tiene dos bloques P1 y P2. Solo necesitamos obtener P2 (obtener P1 es similar). Hemos proporcionado un código esqueleto llamado `manual_attack.py`. Puede usarlo como base para construir su ataque. Explicaremos cada pieza de este código.

Primero, obtengamos el texto cifrado del oráculo. El texto cifrado en esta tarea consiste en dos bloques, y usamos dos `bytearray` de 16 bytes, C1 y C2, para contener el contenido de estos dos bloques.

```python
oracle = PaddingOracle('10.9.0.80', 5000)
# Obtener el IV + Texto cifrado del oráculo
iv_and_ctext = bytearray(oracle.ctext)
IV = iv_and_ctext[00:16]
C1 = iv_and_ctext[16:32]  # 1er bloque de texto cifrado
C2 = iv_and_ctext[32:48]  # 2do bloque de texto cifrado
print("C1: " + C1.hex())
print("C2: " + C2.hex())
```

Como se muestra en la Figura 1 (descifrado CBC), D1 y D2 son la salida del cifrado por bloques AES. Si podemos obtener sus valores, podemos obtener fácilmente el texto plano haciéndoles XOR con el texto cifrado (o IV para el primer bloque). En esta tarea, nos enfocamos en el segundo bloque P2. Por lo tanto, si podemos averiguar los valores de D2, podemos calcular P2 usando `P2 = C1 ⊕ D2`.

No explicaremos los detalles del ataque de oráculo de relleno en esta descripción del laboratorio. Los estudiantes pueden encontrar los detalles en recursos en línea, como Wikipedia (el libro SEED actual no cubre este ataque). La idea general del ataque es enviar al oráculo un texto cifrado con C1 modificado (llamémoslo CC1). Aunque el oráculo no nos dirá el resultado de `D2 ⊕ CC1`, sí nos dice si el resultado tiene un relleno válido o no. Eso abre la puerta para que averigüemos el valor de D2.

Hay 16 bytes en D2, podemos averiguar su valor un byte a la vez. En el código esqueleto, hemos inicializado dos arreglos D2 y CC1. Sus valores iniciales realmente no importan. Su tarea es usar un proceso iterativo para averiguar el valor del arreglo D2. Para cada iteración, necesita construir el arreglo CC1 apropiadamente.

```python
# El valor inicial de D2 no importa. Nuestro trabajo es
# encontrar sus valores correctos.
D2 = bytearray(16)
D2[0] = C1[0]
D2[1] = C1[1]
# ...
D2[15] = C1[15]

# CC1 se usa para reemplazar el bloque C1 en el texto cifrado
# Sus valores deben configurarse apropiadamente en cada ronda
CC1 = bytearray(16)
CC1[0] = 0x00
CC1[1] = 0x00
# ...
CC1[15] = 0x00
```

En cada iteración, nos enfocamos en un byte de CC1. Probamos los 256 valores posibles para ese byte, y enviamos el texto cifrado construido `CC1 + C2` (más el IV) al oráculo, y vemos qué valor hace que el relleno sea válido. Siempre que nuestra construcción sea correcta, habrá un valor válido. Este valor nos ayuda a obtener un byte de D2. El siguiente código se enfoca en K=1. Puede ayudarnos a encontrar el valor de D[15].

```python
K = 1
for i in range(256):
    CC1[16 - K] = i
    status = oracle.decrypt(IV + CC1 + C2)
    if status == "Valid":
        print("Valid: i = 0x{:02x}".format(i))
        print("CC1: " + CC1.hex())
```

Puede usar el código esqueleto como su base, cambiar manualmente el valor de K, usar el resultado de ejecución en cada ronda para establecer D2 acorde, y luego re-ejecutar el programa con un CC1 actualizado para obtener el siguiente byte de D2, es decir, D2[14]. Repitiendo el paso, puede obtener D2[13], D2[12], ..., D2[0]. Una vez que obtenga todo D2, obtiene el valor del texto plano P2.

```python
# Una vez que obtiene los 16 bytes de D2, puede obtener fácilmente P2
P2 = xor(C1, D2)
print("P2: " + P2.hex())
```

**Nota.** Averiguar los 16 bytes de D2 puede ser muy tedioso. Los estudiantes pueden detenerse después de obtener 6 bytes de D2. Eso desbloqueará los últimos 6 bytes del texto plano P2 (incluyendo el relleno). Es suficiente. Aunque los estudiantes pueden escribir código para automatizar todo el proceso, es la intención del laboratorio obligar a los estudiantes a hacerlo manualmente. Por lo tanto, el informe de laboratorio necesita incluir cómo se obtuvo cada byte (para al menos 6 bytes) de D2. En la siguiente tarea, se requerirá a los estudiantes automatizar este proceso.

## 5. Tarea 3: Ataque de oráculo de relleno (Nivel 2)

Hicimos ataques manuales en la tarea anterior. En esta tarea, automatizaremos el proceso de ataque, y esta vez, necesitamos obtener todos los bloques del texto plano. Cuando el contenedor inicia, se iniciarán dos servidores oráculo de relleno, uno para la tarea de Nivel-1, y el otro es para la tarea de Nivel-2, es decir, esta tarea. El servidor de Nivel-2 escucha en el puerto 6000. Aunque la clave y el mensaje secreto están en el código binario del programa oráculo, hemos intentado ofuscarlos, por lo que no será muy fácil encontrarlos desde el binario. Además, conocer el mensaje secreto no ayuda en absoluto al ataque de oráculo de relleno. La calificación de los estudiantes depende de cómo derivan el mensaje secreto usando el ataque de oráculo de relleno, no de si conocen o no el mensaje secreto.

Debe notarse que cada vez que hace una nueva conexión al oráculo, el oráculo generará una nueva clave e IV para cifrar el mensaje secreto (el mensaje sigue siendo el mismo). Por eso verá un texto cifrado diferente. Sin embargo, si permanece dentro de una conexión existente, la clave e IV no cambiarán. Puede escribir un programa para derivar todos los bloques del mensaje secreto en una sola ejecución, pero se le permite escribir su programa para obtener un bloque a la vez. Eventualmente, necesita imprimir todos los bloques. En su informe, necesita incluir su código, junto con las capturas de pantalla de los resultados de ejecución.

## 6. Entrega

Necesita enviar un informe detallado del laboratorio, con capturas de pantalla, para describir lo que ha hecho y lo que ha observado. También necesita proporcionar explicación a las observaciones que sean interesantes o sorprendentes. Por favor también liste los fragmentos de código importantes seguidos de explicación. Simplemente adjuntar código sin ninguna explicación no recibirá créditos.

## 7. Agradecimientos

Nos gustaría agradecer la contribución hecha por las siguientes personas y organizaciones:

- Jiamin Shen desarrolló lo siguiente: el código que corre dentro del contenedor, la versión inicial de la tarea de ataque de oráculo de relleno.
- La US National Science Foundation proporcionó financiamiento para el proyecto SEED desde 2002 hasta 2020.
- Syracuse University proporcionó los recursos para el proyecto SEED desde 2001 en adelante.
