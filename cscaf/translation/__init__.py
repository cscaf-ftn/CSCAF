"""Translation of the job advertisements into English, paragraph by paragraph.

The crawler's own translation failed in three ways, so the
affected advertisements are exported one paragraph per row, translated by a machine translation
service and rebuilt. Working per paragraph is what keeps the structure of the advertisement and makes
a mixed-language advertisement tractable, because each paragraph is detected on its own.

The service is interchangeable: `MachineTranslator` is the interface and `AzureTranslator` the implementation,
and `Translator` sends a service only the lines the English check flags.
"""
from cscaf.translation.azure_translator import AzureTranslator
from cscaf.translation.machine_translator import MachineTranslator
from cscaf.translation.rate_limiter import RateLimiter
from cscaf.translation.translator import Translator
from cscaf.translation.usage_ledger import UsageLedger

__all__ = ["AzureTranslator", "MachineTranslator", "RateLimiter", "Translator", "UsageLedger"]
