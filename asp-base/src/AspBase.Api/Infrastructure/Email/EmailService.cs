using System.Net;
using System.Net.Mail;
using AspBase.Api.Infrastructure.Options;
using Microsoft.Extensions.Options;

namespace AspBase.Api.Infrastructure.Email;

public interface IEmailService
{
    Task SendAsync(string subject, string to, string textBody, string? htmlBody = null, CancellationToken ct = default);
    Task SendPasswordResetAsync(string to, string name, string code, CancellationToken ct = default);
    Task SendWelcomeAsync(string to, string name, CancellationToken ct = default);
}

/// <summary>
/// SMTP email service, the .NET counterpart of the DRF <c>EmailService</c>. Templates match
/// the original text/HTML bodies. Delivery is normally enqueued via <see cref="EmailQueue"/>
/// so request threads are not blocked (the Celery equivalent).
/// </summary>
public class EmailService(IOptions<EmailOptions> options, ILogger<EmailService> logger) : IEmailService
{
    private readonly EmailOptions _opt = options.Value;

    public async Task SendAsync(string subject, string to, string textBody, string? htmlBody = null, CancellationToken ct = default)
    {
        using var message = new MailMessage
        {
            From = new MailAddress(_opt.FromEmail),
            Subject = subject,
            Body = htmlBody ?? textBody,
            IsBodyHtml = htmlBody is not null,
        };
        message.To.Add(to);
        if (htmlBody is not null)
        {
            message.AlternateViews.Add(AlternateView.CreateAlternateViewFromString(textBody, null, "text/plain"));
            message.AlternateViews.Add(AlternateView.CreateAlternateViewFromString(htmlBody, null, "text/html"));
        }

        using var client = new SmtpClient(_opt.Host, _opt.Port)
        {
            EnableSsl = _opt.UseTls,
            Credentials = string.IsNullOrEmpty(_opt.User) ? null : new NetworkCredential(_opt.User, _opt.Password),
        };

        await client.SendMailAsync(message, ct);
        logger.LogInformation("Email sent to {Recipient}: {Subject}", to, subject);
    }

    public Task SendPasswordResetAsync(string to, string name, string code, CancellationToken ct = default)
    {
        const string subject = "Password Reset Code";
        var text = $"Hello {name},\n\nYour password reset code is: {code}\n\n" +
                   "If you didn't request this, please ignore this email.";
        var html = $"<p>Hello <strong>{name}</strong>,</p>" +
                   "<p>Your password reset code is:</p>" +
                   $"<h2 style='letter-spacing:4px'>{code}</h2>" +
                   "<p>If you didn't request a password reset, you can safely ignore this email.</p>";
        return SendAsync(subject, to, text, html, ct);
    }

    public Task SendWelcomeAsync(string to, string name, CancellationToken ct = default)
    {
        const string subject = "Welcome!";
        var text = $"Welcome {name}! Your account has been created successfully.";
        var html = $"<h2>Welcome, {name}!</h2>" +
                   "<p>Your account has been created successfully.</p>" +
                   "<p>You can now log in and start using the platform.</p>";
        return SendAsync(subject, to, text, html, ct);
    }
}
