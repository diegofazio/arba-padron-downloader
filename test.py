import pycurl
import sys
from io import BytesIO
from bs4 import BeautifulSoup

URL_LOGIN = "https://sso.arba.gov.ar/Login/login?service=https://dfe.arba.gov.ar:443/DomicilioElectronico/dfeSetUpInicio.do"
USER_AGENT = "Mozilla/4.0 (compatible; PROG 1.0; Windows NT 5.0; YComp 5.0.2.4)"
HEADERS = [
    "Content-Type: application/x-www-form-urlencoded",
    f"User-Agent: {USER_AGENT}",
    "Referer: https://sso.arba.gov.ar/Login/login",
    "Origin: https://sso.arba.gov.ar",
    "Connection: keep-alive",
    "Accept: */*",
    "Accept-Encoding: gzip, deflate, br"
]

def perform_curl(curl, url, post_data=None, cookie=None):
   buffer = BytesIO()
   curl.setopt(pycurl.URL, url)
   curl.setopt(pycurl.HTTPHEADER, HEADERS)
   curl.setopt(pycurl.SSL_VERIFYPEER, 0)
   curl.setopt(pycurl.SSL_VERIFYHOST, 0)
   curl.setopt(pycurl.WRITEDATA, buffer)
   curl.setopt(pycurl.COOKIEFILE, "") 
   curl.setopt(pycurl.COOKIEJAR, "")  
   
   if post_data:
      curl.setopt(pycurl.POST, 1)
      curl.setopt(pycurl.POSTFIELDS, post_data)
   
   if cookie:
      curl.setopt(pycurl.COOKIE, cookie)

   try:
      curl.perform()
      response_code = curl.getinfo(pycurl.RESPONSE_CODE)
      if response_code == 200:
         return buffer.getvalue()
      else:
         raise Exception(f"Curl error: HTTP response code {response_code}")
   except pycurl.error as e:
        raise Exception(f"Curl Error: {str(e)}")

def main():
   cCuit = "xxxxxxxxxxx"
   cPass = "password"
   cFile = "PadronRGS112024.zip"

   curl = pycurl.Curl()

   try:
      cOut = perform_curl(curl, URL_LOGIN)
      soup = BeautifulSoup(cOut, 'html.parser')
      cLt = soup.find('input', {'name': 'lt'})['value'] if soup.find('input', {'name': 'lt'}) else ""
      print(cLt)
   except Exception as e:
      print(f"Error en el primer login: {str(e)}")
      sys.exit()

   cPost = (
      f"CUIT={cCuit}&clave_Cuit={cPass}&userComponent=op_Cuit&selectLoguin=op_Cuit"
      f"&lt={cLt}&username={cCuit}&password={cPass}"
   )
   try:
      cOut = perform_curl(curl, URL_LOGIN, post_data=cPost)
      cookies = curl.getinfo(pycurl.INFO_COOKIELIST)

      cCookie = None
      
      if cookies:
         for cookie in cookies:
               if "JSESSIONID" in cookie:
                  cCookie = cookie.split("JSESSIONID")[1].strip()
                  break

      if cCookie:
         print("JSESSIONID:", cCookie)
      else:
         print("Error en inicio de sesión")
         sys.exit()
         
      if not cCookie:
         print("Error en inicio de sesión")
         sys.exit()

   except Exception as e:
      print(f"Error en el segundo login: {str(e)}")
      sys.exit()

   soup = BeautifulSoup(cOut, 'html.parser')
   cService = soup.find('input', {'name': 'service'})['value'] if soup.find('input', {'name': 'service'}) else ""
   cSt = soup.find('input', {'name': 'ticket'})['value'] if soup.find('input', {'name': 'ticket'}) else "Ticket de acceso vacio"
   if cSt == "Ticket de acceso vacio":
      print("Error: Ticket de acceso vacio")
      sys.exit()

   print(cService)
   print(cSt)

   cPost = f"userComponent=op_Cuit&service={cService}&ticket={cSt}&tipoOjeto="
   try:
      cOut = perform_curl(curl, cService, post_data=cPost, cookie=f"JSESSIONID={cCookie}")
   except Exception as e:
      print(f"Error al enviar el post de servicio: {str(e)}")
      sys.exit()

   cPost = f"archivo={cFile}"
   
   print("Descargando archivo...")
   
   with open(cFile, "wb") as file:
      try:
         cOut = perform_curl(curl, "https://dfe.arba.gov.ar/DomicilioElectronico/dfeDescargarPadron.do?dispatch=descargar", post_data=cPost, cookie=f"JSESSIONID={cCookie}")
         file.write(cOut)
         print("Descarga completada.")
      except Exception as e:
         print(f"Error en la descarga: {str(e)}")
         sys.exit()
      finally:
            curl.close()

if __name__ == "__main__":
    main()
