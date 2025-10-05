import mailtrap as mt

print("🚀 Iniciando envío de correo...")

try:
    # Crea el cliente Mailtrap con tu token
    client = mt.MailtrapClient(token="68e9dd4d315e77333c07c7967898542c")

    # Crea el mensaje
    mail = mt.Mail(
        sender=mt.Address(email="hello@demomailtrap.io", name="Mailtrap Test"),
        to=[mt.Address(email="romerondan123@gmail.com")],
        subject="You are awesome!",
        text="Congrats for sending a test email with Mailtrap!",
        category="Integration Test",
    )

    print("📨 Enviando mensaje...")
    response = client.send(mail)
    print("✅ Correo enviado con éxito!")
    print(response)

except Exception as e:
    print("❌ Error al enviar el correo:")
    print(e)
