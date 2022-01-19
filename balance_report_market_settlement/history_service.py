from .models import Report, HistoryBalance, BalanceFields, PriorizedCliq
from datetime import datetime
from SmartEnergy.handler_logging import HandlerLog
from .utils import get_local_timezone


class HistoryService:
    logger = HandlerLog()
    def __init__(self):
        super().__init__()

    def save_history_balance(self, balance, justification, user, old_balance=None):
        try:
            if old_balance is None:
                old_balance = Report.objects.filter(month__exact=balance.month, year__exact=balance.year).latest('id')
            history = HistoryBalance.objects.filter(id_report__exact=balance.id).latest('id')
            self.update_history(balance, old_balance, justification, user)

        except Report.DoesNotExist:
            self.new_history(balance, justification, user)

        except HistoryBalance.DoesNotExist:
            first_history_of_the_month = HistoryBalance.objects.filter(id_report__month=balance.month, id_report__year=balance.year)
            if first_history_of_the_month.exists():
                self.update_history(balance, old_balance, justification, user)
            else:
                self.new_history(balance, justification, user)

        except Exception:
            self.logger.error('Failed to try to save History Balance!')
            return balance

    def create_history(self, balance, justification, user):
        history = HistoryBalance()

        history.justification = justification
        history.create_date = datetime.now(get_local_timezone())
        history.username = user
        history.id_report = balance
        
        history.month = True
        history.year = True
        history.id_rcd = True
        history.status = True
        history.gsf = True
        history.pld_n = True
        history.pld_ne = True
        history.pld_s = True
        history.pld_seco = True
        history.priorized_cliq = True

        return history

    def new_history(self, balance, justification, user):
        history = self.create_history(balance, justification, user)
        history.save()

    def update_history(self, balance, old_balance, justification, user):
        balance_fields = BalanceFields.objects.filter(id_report__exact=balance.id).latest('id')
        old_balance_fields = BalanceFields.objects.filter(id_report__exact=old_balance.id).latest('id')
        priorized_cliq = PriorizedCliq.objects.filter(id_report__exact=balance.id)
        old_priorized_cliq = PriorizedCliq.objects.filter(id_report__exact=old_balance.id)

        history = self.create_history(balance, justification, user)
        history.month = not (balance.month == old_balance.month)
        history.year = not (balance.year == old_balance.year)
        history.id_rcd = not (balance.id_reference.id == old_balance.id_reference.id)
        history.status = not (balance.status == old_balance.status)
        history.gsf = not (balance_fields.gsf == old_balance_fields.gsf)
        history.pld_n = not (balance_fields.pld_n == old_balance_fields.pld_n)
        history.pld_ne = not (balance_fields.pld_ne == old_balance_fields.pld_ne)
        history.pld_seco = not (balance_fields.pld_seco == old_balance_fields.pld_seco)
        history.pld_s = not (balance_fields.pld_s == old_balance_fields.pld_s)
        history.priorized_cliq = self.compare_cliq(priorized_cliq, old_priorized_cliq)

        history.save()

    def compare_cliq(self, priorized_cliq, old_priorized_cliq):
        concat_cliq = ''
        for cliq in priorized_cliq:
            concat_cliq = concat_cliq + str(cliq.contract_name)

        concat_cliq_old = ''
        for cliq_old in old_priorized_cliq:
            concat_cliq_old = concat_cliq_old + str(cliq_old.contract_name)
        
        return not (concat_cliq == concat_cliq_old)
