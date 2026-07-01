using System.Threading.Channels;

namespace AspBase.Api.Infrastructure.Email;

/// <summary>
/// In-process background email queue. Endpoints enqueue a job and return immediately;
/// <see cref="EmailBackgroundService"/> drains the channel and delivers with retries.
/// This is the lightweight replacement for the Celery + Redis email pipeline
/// (<c>send_welcome_email.delay(...)</c>, <c>send_password_reset_email.delay(...)</c>).
/// </summary>
public class EmailQueue
{
    private readonly Channel<Func<IEmailService, CancellationToken, Task>> _channel =
        Channel.CreateUnbounded<Func<IEmailService, CancellationToken, Task>>();

    public ValueTask EnqueueAsync(Func<IEmailService, CancellationToken, Task> job) => _channel.Writer.WriteAsync(job);

    public IAsyncEnumerable<Func<IEmailService, CancellationToken, Task>> ReadAllAsync(CancellationToken ct) =>
        _channel.Reader.ReadAllAsync(ct);

    // Convenience helpers mirroring the Celery task names.
    public ValueTask QueueWelcomeEmail(string to, string name) =>
        EnqueueAsync((svc, ct) => svc.SendWelcomeAsync(to, name, ct));

    public ValueTask QueuePasswordResetEmail(string to, string name, string code) =>
        EnqueueAsync((svc, ct) => svc.SendPasswordResetAsync(to, name, code, ct));
}
