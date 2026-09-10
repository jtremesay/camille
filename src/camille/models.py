# Camille - An AI assistant
# Copyright (C) Jonathan Tremesaygues <jonathan.tremesaygues@slaanesh.org>
#
# This program is free software: you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program. If not, see <https://www.gnu.org/licenses/>.
from uuid import uuid7

from django.contrib.auth.models import AbstractUser
from django.db import models
from django_rls_tenants import RLSProtectedModel


class Tenant(models.Model):
    uuid = models.UUIDField(primary_key=True, editable=False, default=uuid7)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    name = models.CharField(max_length=255)

    def __str__(self) -> str:
        return self.name


class User(AbstractUser, RLSProtectedModel):
    # Override the auto-generated tenant FK to allow null (for admins)
    tenant = models.ForeignKey(
        Tenant,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )

    @property
    def is_tenant_admin(self) -> bool:
        """Admins bypass RLS and see all tenants."""
        return self.is_superuser

    @property
    def rls_tenant_id(self) -> UUID | None:
        """Return the tenant PK for RLS filtering."""
        return self.tenant_uuid or None
