from navmazing import NavigateToAttribute, NavigateToSibling
from widgetastic.utils import Fillable

from cfme.base.ui import Server

from cfme.base.ui import BaseLoggedInPage
from cfme.utils import version
from cfme.common.provider import BaseProvider
from cfme.common.provider_views import (PhysicalProviderAddView,
                                        PhysicalProviderDetailsView,
                                        PhysicalProviderEditView)
from cfme.utils.appliance import Navigatable
from cfme.utils.appliance.implementations.ui import navigator, CFMENavigateStep
from cfme.utils.pretty import Pretty
from cfme.utils.varmeth import variable
from cfme.utils.appliance.implementations.ui import navigate_to
from cfme.fixtures import pytest_selenium as sel

from cfme.utils.log import logger


class PhysicalProvider(Pretty, BaseProvider, Fillable):
    """
    Abstract model of an infrastructure provider in cfme. See VMwareProvider or RHEVMProvider.
    """
    provider_types = {}
    category = "physical"
    pretty_attrs = ['name']
    STATS_TO_MATCH = ['num_server']
    string_name = "Physical Infrastructure"
    page_name = "infrastructure"
    db_types = ["PhysicalInfraManager"]

    def __init__(
            self, appliance=None, name=None, key=None, endpoints=None):
        Navigatable.__init__(self, appliance=appliance)
        self.endpoints = self._prepare_endpoints(endpoints)
        self.name = name
        self.key = key

    @variable(alias='db')
    def num_server(self):
        provider = self.appliance.rest_api.collections.providers.find_by(name=self.name)[0]
        num_server = 0
        for server in self.appliance.rest_api.collections.physical_servers:
            if server['ems_id'] == provider.id:
                num_server += 1
        return num_server

    @num_server.variant('ui')
    def num_server_ui(self):
        try:
            num = self.get_detail("Relationships", 'Physical Servers')
        except sel.NoSuchElementException:
            logger.error("Couldn't find number of hosts using key [Hosts] trying Nodes")
            num = self.get_detail("Relationships", 'Nodes')
        return int(num)

    def delete(self, cancel=True):
        """
        Deletes a provider from CFME

        Args:
            cancel: Whether to cancel the deletion, defaults to True
        """
        view = navigate_to(self, 'Details')
        item_title = version.pick({'5.9': 'Remove this Infrastructure Provider from Inventory',
                                   version.LOWEST: 'Remove this Infrastructure Provider'})
        view.toolbar.configuration.item_select(item_title.format(self.string_name),
                                               handle_alert=not cancel)
        if not cancel:
            msg = ('Delete initiated for 1 {} Provider from '
                   'the {} Database'.format(self.string_name, self.appliance.product_name))
            view.flash.assert_success_message(msg)


@navigator.register(Server, 'PhysicalProviders')
@navigator.register(PhysicalProvider, 'All')
class All(CFMENavigateStep):
    # This view will need to be created
    VIEW = BaseLoggedInPage
    prerequisite = NavigateToAttribute('appliance.server', 'LoggedIn')

    def step(self):
        self.prerequisite_view.navigation.select('Compute', 'Physical Infrastructure', 'Providers')

    def resetter(self):
        # Reset view and selection
        pass


@navigator.register(PhysicalProvider, 'Details')
class Details(CFMENavigateStep):
    VIEW = PhysicalProviderDetailsView
    prerequisite = NavigateToSibling('All')

    def step(self):
        self.prerequisite_view.entities.get_entity(by_name=self.obj.name, surf_pages=True).click()

    def resetter(self):
        # Reset view and selection
        pass


@navigator.register(PhysicalProvider, 'Edit')
class Edit(CFMENavigateStep):
    VIEW = PhysicalProviderEditView
    prerequisite = NavigateToSibling('Details')

    def step(self):
        self.prerequisite_view.toolbar.configuration.item_select(
            'Edit this Infrastructure Provider')


@navigator.register(PhysicalProvider, 'Add')
class Add(CFMENavigateStep):
    VIEW = PhysicalProviderAddView
    prerequisite = NavigateToSibling('All')

    def step(self):
        self.prerequisite_view.toolbar.configuration.item_select(
            'Add a New Infrastructure Provider'
        )
