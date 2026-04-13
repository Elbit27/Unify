from allauth.account.adapter import DefaultAccountAdapter
from .models import EmailVerificationCode


class CustomAccountAdapter(DefaultAccountAdapter):
    def send_confirmation_mail(self, request, emailconfirmation, signup):
        # 1. Генерируем твой 6-значный код
        user = emailconfirmation.email_address.user
        code = EmailVerificationCode.generate_code(user)

        # 2. Формируем контекст (копируем логику allauth + добавляем своё)
        ctx = {
            "user": user,
            "activate_url": self.get_email_confirmation_url(request, emailconfirmation),
            "verification_code": code,  # ВОТ ОН, ТВОЙ КОД!
        }

        # Выбираем шаблон
        if signup:
            email_template = "account/email/email_confirmation_signup"
        else:
            email_template = "account/email/email_confirmation"

        # 3. Отправляем письмо через метод адаптера
        # (он сам добавит .txt или .html к названию шаблона)
        self.send_mail(email_template, emailconfirmation.email_address.email, ctx)

        print(f"--- ПИСЬМО ОТПРАВЛЕНО. КОД: {code} ---")