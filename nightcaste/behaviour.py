import importlib
import input


class BehaviourManager:
    """The Bahavoiur manager stores component behevoiurs."""

    def __init__(self, event_manager, entitiy_manager, config=None):
        self.event_manager = event_manager
        self.entity_manager = entitiy_manager
        self.behaviors = {}
        if config is not None:
            self.configure(config)

    def configure(self, config):
        if 'component_behaviours' in config:
            for behaviour in config['component_behaviours']:
                self.add_comp_behavoir_from_name(
                    behaviour['component_type'],
                    behaviour['name'])

    def add_comp_behavoir_from_name(self, component_type, behaviour_name):
        module = importlib.import_module('nightcaste.behaviour')
        behaviour_class = getattr(module, behaviour_name)
        behaviour = behaviour_class(self.event_manager, self.entity_manager)
        self.add_component_bevaiour(component_type, behaviour)

    def add_component_bevaiour(self, component_type, behaviour):
        self.behaviors.update({component_type: behaviour})

    def update(self, round, delta_time):
        for component_type, behaviour in self.behaviors.iteritems():
            components = self.entity_manager.get_all_of_type(component_type)
            for entity, component in components.iteritems():
                behaviour.entity = entity
                behaviour.component = component
                behaviour.update(round, delta_time)


class EntityComponentBehaviour:

    def __init__(self, event_manager, entitiy_manager):
        self.entity_manager = entitiy_manager
        self.event_manager = event_manager
        self.entity = None
        self.component = None

    def update(self, round, delta_time):
        pass
