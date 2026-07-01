namespace AspBase.Api.Infrastructure.Email;

/// <summary>
/// Hosted service that drains <see cref="EmailQueue"/> and sends each message, retrying up to
/// three times with a 60-second delay — the same policy as the Celery <c>@shared_task</c>
/// definitions (<c>max_retries=3, default_retry_delay=60</c>).
/// </summary>
public class EmailBackgroundService(
    EmailQueue queue,
    IServiceScopeFactory scopeFactory,
    ILogger<EmailBackgroundService> logger) : BackgroundService
{
    private const int MaxRetries = 3;
    private static readonly TimeSpan RetryDelay = TimeSpan.FromSeconds(60);

    protected override async Task ExecuteAsync(CancellationToken stoppingToken)
    {
        await foreach (var job in queue.ReadAllAsync(stoppingToken))
        {
            _ = ProcessAsync(job, stoppingToken);
        }
    }

    private async Task ProcessAsync(Func<IEmailService, CancellationToken, Task> job, CancellationToken ct)
    {
        for (var attempt = 1; attempt <= MaxRetries; attempt++)
        {
            try
            {
                using var scope = scopeFactory.CreateScope();
                var emailService = scope.ServiceProvider.GetRequiredService<IEmailService>();
                await job(emailService, ct);
                return;
            }
            catch (Exception ex)
            {
                logger.LogError(ex, "Failed to send email (attempt {Attempt}/{Max})", attempt, MaxRetries);
                if (attempt == MaxRetries) return;
                try { await Task.Delay(RetryDelay, ct); }
                catch (OperationCanceledException) { return; }
            }
        }
    }
}
