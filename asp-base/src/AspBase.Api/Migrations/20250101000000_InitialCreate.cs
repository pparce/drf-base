using Microsoft.EntityFrameworkCore.Migrations;
using Npgsql.EntityFrameworkCore.PostgreSQL.Metadata;

#nullable disable

namespace AspBase.Api.Migrations;

/// <inheritdoc />
public partial class InitialCreate : Migration
{
    /// <inheritdoc />
    protected override void Up(MigrationBuilder migrationBuilder)
    {
        migrationBuilder.CreateTable(
            name: "users",
            columns: table => new
            {
                Id = table.Column<long>(type: "bigint", nullable: false)
                    .Annotation("Npgsql:ValueGenerationStrategy", NpgsqlValueGenerationStrategy.IdentityByDefaultColumn),
                Email = table.Column<string>(type: "character varying(255)", maxLength: 255, nullable: false),
                PasswordHash = table.Column<string>(type: "text", nullable: true),
                FirstName = table.Column<string>(type: "character varying(255)", maxLength: 255, nullable: true),
                LastName = table.Column<string>(type: "character varying(255)", maxLength: 255, nullable: true),
                IsActive = table.Column<bool>(type: "boolean", nullable: false),
                IsStaff = table.Column<bool>(type: "boolean", nullable: false),
                IsSuperuser = table.Column<bool>(type: "boolean", nullable: false),
                IsCustomer = table.Column<bool>(type: "boolean", nullable: false),
                IsValidate = table.Column<bool>(type: "boolean", nullable: false),
                RestoreCode = table.Column<string>(type: "character varying(8)", maxLength: 8, nullable: true),
                Avatar = table.Column<string>(type: "text", nullable: true),
                ReceiveNews = table.Column<bool>(type: "boolean", nullable: false),
                LastLogin = table.Column<DateTime>(type: "timestamp with time zone", nullable: true),
                CreatedAt = table.Column<DateTime>(type: "timestamp with time zone", nullable: false),
                UpdatedAt = table.Column<DateTime>(type: "timestamp with time zone", nullable: false)
            },
            constraints: table => table.PrimaryKey("PK_users", x => x.Id));

        migrationBuilder.CreateTable(
            name: "images",
            columns: table => new
            {
                Id = table.Column<long>(type: "bigint", nullable: false)
                    .Annotation("Npgsql:ValueGenerationStrategy", NpgsqlValueGenerationStrategy.IdentityByDefaultColumn),
                ImagePath = table.Column<string>(type: "text", nullable: true),
                Height = table.Column<int>(type: "integer", nullable: false),
                Width = table.Column<int>(type: "integer", nullable: false),
                ImageHash = table.Column<string>(type: "character varying(64)", maxLength: 64, nullable: false),
                CreatedAt = table.Column<DateTime>(type: "timestamp with time zone", nullable: false),
                UpdatedAt = table.Column<DateTime>(type: "timestamp with time zone", nullable: false)
            },
            constraints: table => table.PrimaryKey("PK_images", x => x.Id));

        migrationBuilder.CreateIndex(
            name: "IX_users_Email",
            table: "users",
            column: "Email",
            unique: true);
    }

    /// <inheritdoc />
    protected override void Down(MigrationBuilder migrationBuilder)
    {
        migrationBuilder.DropTable(name: "images");
        migrationBuilder.DropTable(name: "users");
    }
}
