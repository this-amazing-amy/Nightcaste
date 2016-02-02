"""The model represents backing storage for entities."""


class EntityManager:
    """The EntityManager is the interface for all systems to create and retrieve
    entites e.g their components"""

    def __init__(self):
        self.last_id = -1l
        self.component_manager = ComponentManager()
        self.blue_print_manager = BluePrintManager()

    def create_entity(self):
        self.last_id += 1l
        return self.last_id

    def create_entity_from_configuration(self, configuration):
        entity = self.create_entity()
        self.component_manager.add_components(entity, configuration)
        return entity

    def create_entity_from_blue_print(self, blue_print):
        configuration = self.blue_print_manager.create_configuration(blue_print)
        return self.create_entity_from_configuration(configuration)


class ComponentManager:

    def add_components(entity, configuration):
        "TODO: Dummy"
        pass


class BluePrintManager:
    """Points the a blue print file which contains information about the
    structure of an entity"""

    def create_configuration(self, blue_print):
        """TODO: either load prefetched configuration or lazy load it here.
        Since loading a bluebrint involves IO it may be advisable to prefetch
        the configuration into a dictionary are at least cache on first
        access"""
        return EntityConfiguration()


class EntityConfiguration:
    """Stores the necessary information the construct an entity

        TODO:
            - Select better data structure than nested dictionaries
              => may be a combined key 'Position.x': value
              => Complete object structure: Component with a List of Attributes
                 an Attribute is a key value pair
            - Provide easy acceess to all information

    """

    def __init__(self):
        self.components = {}

    def add_attribute(self, component, name, value):
        """Add an attribute for the specified component

            TODO: May select better structure than dictionaries"""
        if component not in self.components:
            self.components.update({component: {name: value}})
        else:
            component_attributes = self.components[component]
            component_attributes.update({name: value})

    def get_attributes(self, component):
        if component not in self.components:
            return {}

        return self.components[component]
