from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from jose import jwt, JWTError
from datetime import datetime, timedelta
from passlib.context import CryptContext

from app.core.config import settings
from app.core.database import get_db
from app.core.security import verify_password, create_access_token, create_refresh_token
from app.models.admin_user import AdminUser
from app.api.deps import get_current_active_admin
from app.services.email_service import email_service

router = APIRouter()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class LoginRequest(BaseModel):
    email: str
    password: str

class RefreshTokenRequest(BaseModel):
    refresh_token: str

class ForgotPasswordRequest(BaseModel):
    email: EmailStr

class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str


@router.post("/login")
def admin_login(form_data: LoginRequest, db: Session = Depends(get_db)):
    """
    Authenticate admin user and return access & refresh tokens.
    """
    user = db.query(AdminUser).filter(AdminUser.email == form_data.email).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )
    if not getattr(user, "is_active", True):
        raise HTTPException(status_code=400, detail="Inactive admin user")
    
    access_token = create_access_token(data={"sub": user.email, "type": "access"})
    refresh_token = create_refresh_token(data={"sub": user.email, "type": "refresh"})
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }


@router.post("/refresh")
def refresh_access_token(payload_data: RefreshTokenRequest):
    """
    Issues a new access token using a valid refresh token.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired refresh token",
    )
    try:
        payload = jwt.decode(
            payload_data.refresh_token, 
            settings.SECRET_KEY, 
            algorithms=[getattr(settings, "ALGORITHM", "HS256")]
        )
        if payload.get("type") != "refresh":
            raise credentials_exception
            
        email: str = payload.get("sub")
        if not email:
            raise credentials_exception
            
        access_token_expires = timedelta(minutes=getattr(settings, "ACCESS_TOKEN_EXPIRE_MINUTES", 30))
        expire = datetime.utcnow() + access_token_expires
        
        new_access_token = jwt.encode(
            {"sub": email, "exp": expire, "type": "access"}, 
            settings.SECRET_KEY, 
            algorithm=getattr(settings, "ALGORITHM", "HS256")
        )
        return {"access_token": new_access_token, "token_type": "bearer"}
        
    except JWTError:
        raise credentials_exception


@router.post("/logout")
def logout_admin(admin: AdminUser = Depends(get_current_active_admin)):
    """
    Logs out the current authenticated admin.
    """
    return {"message": "Successfully logged out. Please clear your tokens on the client side."}


@router.post("/forgot-password")
def forgot_password(
    data: ForgotPasswordRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """
    Generates a password reset token and emails it to the admin.
    Always returns the same generic response to prevent user enumeration.
    """
    # Always return the same message to prevent user enumeration
    generic_response = {"message": "If the email exists, a password reset link has been sent."}

    admin = db.query(AdminUser).filter(AdminUser.email == data.email).first()
    if not admin:
        return generic_response

    expire = datetime.utcnow() + timedelta(minutes=15)
    reset_token = jwt.encode(
        {"sub": admin.email, "exp": expire, "type": "reset"},
        settings.SECRET_KEY,
        algorithm=getattr(settings, "ALGORITHM", "HS256"),
    )

    # Send the reset token by email only – never include it in the response.
    frontend_url = getattr(settings, "FRONTEND_URL", "")
    reset_link = f"{frontend_url}/admin/reset-password?token={reset_token}"

    def _send_reset_email():
        try:
            import smtplib, httpx
            from email.message import EmailMessage as StdEmailMessage
            from app.services.email_service import render_template

            context = {
                "name": getattr(admin, "name", admin.email),
                "reset_link": reset_link,
                "expiry_minutes": 15,
            }
            provider = getattr(settings, "EMAIL_PROVIDER", "smtp").lower()
            subject = "BrainMint Admin – Password Reset Request"
            html_body = render_template("password_reset.html", context)
            plain = (
                f"Hi {context['name']},\n\n"
                f"Click the link below to reset your password (expires in 15 min):\n{reset_link}\n\n"
                "If you did not request this, you can safely ignore this email."
            )

            if provider == "sendgrid":
                headers = {"Authorization": f"Bearer {settings.SENDGRID_API_KEY}", "Content-Type": "application/json"}
                payload = {
                    "personalizations": [{"to": [{"email": admin.email}]}],
                    "from": {"email": settings.EMAILS_FROM_EMAIL or settings.SMTP_USER},
                    "subject": subject,
                    "content": [{"type": "text/html", "value": html_body or plain}],
                }
                httpx.post("https://api.sendgrid.com/v3/mail/send", json=payload, headers=headers, timeout=10.0).raise_for_status()
            elif provider == "mailgun":
                httpx.post(
                    f"https://api.mailgun.net/v3/{settings.MAILGUN_DOMAIN}/messages",
                    data={"from": f"BrainMint <{settings.EMAILS_FROM_EMAIL or settings.SMTP_USER}>", "to": [admin.email], "subject": subject, "html": html_body or plain},
                    auth=("api", settings.MAILGUN_API_KEY), timeout=10.0,
                ).raise_for_status()
            else:
                use_ssl = getattr(settings, "SMTP_SSL", False)
                smtp_cls = smtplib.SMTP_SSL if use_ssl else smtplib.SMTP
                msg = StdEmailMessage()
                msg["Subject"] = subject
                msg["From"] = settings.EMAILS_FROM_EMAIL or settings.SMTP_USER
                msg["To"] = admin.email
                msg.set_content(plain)
                if html_body:
                    msg.add_alternative(html_body, subtype="html")
                with smtp_cls(settings.SMTP_HOST, settings.SMTP_PORT) as server:
                    if not use_ssl and getattr(settings, "SMTP_TLS", True):
                        server.starttls()
                    if settings.SMTP_USER and settings.SMTP_PASSWORD:
                        server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
                    server.send_message(msg)
        except Exception:
            import logging
            logging.getLogger(__name__).exception("Failed to send password-reset email to %s", admin.email)

    background_tasks.add_task(_send_reset_email)
    return generic_response


@router.post("/reset-password")
def reset_password(data: ResetPasswordRequest, db: Session = Depends(get_db)):
    """
    Resets the admin password using the provided reset token.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Invalid or expired password reset token",
    )
    try:
        payload = jwt.decode(
            data.token, 
            settings.SECRET_KEY, 
            algorithms=[getattr(settings, "ALGORITHM", "HS256")]
        )
        if payload.get("type") != "reset":
            raise credentials_exception
            
        email: str = payload.get("sub")
        admin = db.query(AdminUser).filter(AdminUser.email == email).first()
        if not admin:
            raise credentials_exception
            
        admin.hashed_password = pwd_context.hash(data.new_password)
        db.commit()
        
        return {"message": "Password has been successfully reset."}
        
    except JWTError:
        raise credentials_exception