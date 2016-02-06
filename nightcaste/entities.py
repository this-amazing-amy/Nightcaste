"""The model represents backing storage for entities."""
import components


class EntityManager:
    """The EntityManager is the interface for all systems to create and retrieve
    entites e.g their components"""

    def __init__(self):
        self.last_id = -1
        self.component_manager = ComponentManager()
        self.blueprint_manager = BlueprintManager()

    def create_entity(self):
        """Creates a new empty entity woth no components associated.

            Returns:
                The new entity identifier.

        """
        self.last_id += 1
        return self.last_id

    def create_entity_from_configuration(self, configuration):
        """Constructs a new entity with the components and properties specified
        in the configuration.

            Args:
                configuration (EntityConfiguration): The configuration from
                    which the components are constructed.

            Returns:
                The new entity identifier.

        """
        entity = self.create_entity()
        self.component_manager.add_components(entity, configuration)
        return entity

    def create_entity_from_blueprint(self, blueprint):
        """Constructs a new entity by creating a configuration from a blueprint.

            Args:
                blueprint (str): The name of the blueprint.

            Returns:
                The new entity identifier.

        """
        configuration = self.blueprint_manager.create_configuration(blueprint)
        return self.create_entity_from_configuration(configuration)

    def destroy_entity(self, entity):
        """Removes all components which belong to the given entity.

            Args:
                entity (object): The entity to destroy.

        """
        self.component_manager.remove_components(entity)

    def get_entity_component(self, entity, component_type):
        """Searches the specified component type for the given entity.

            Args:
                entity (object): The entity identifier.
                component_type (str): The component type to search for.

            Returns:
                The specified entity component or None in case the component
                could not be found.

        """
        return self.component_manager.get_component(entity, component_type)

    def get_all_of_type(self, component_type):
        """Get all components of the specified type.

            Args:
                component_type (str): The component type to retrieve.

            Returns:
                A dictionary in the form of {entity: component}.

        """
        return self.component_manager.get_all_of_type(component_type)

    def get_components_for_entities(self, entity_list, component_type):
        """Get the components of the specified type and for the specified entity
        list.

            Args:
                entity_list: List or dictionary containing entity identifiers.
                component_type (str): The component type to return.

            Returns:
                A dictionary in the form of {entity: component}.

        """
        return {k: v for k, v in self.get_all_of_type(
            component_type).iteritems() if k in entity_list}


class ComponentManager:
    """ The Component manager stores the components for all entities, which are
    only represented through an internal entitiy identifier."""

    def __init__(self):
        # Two-dimensional dictionary holding the components of all entities
        # {component_type: {entity_id: Component}}
        self.components = {}

    def add_component(self, entity_id, component):
        """Adds the specified component for the given entity the the component
        database."""
        component_type = component.type()
        component_dict = self.components.get(component_type)
        if (component_dict is None):
            component_dict = {}
            self.components[component_type] = component_dict
        component_dict[entity_id] = component

    def add_components(self, entity_id, configuration):
        """Create and add components based on the given configuration."""
        for component_name, attributes in configuration.components.iteritems():
            component = getattr(components, component_name)()

            "Add all attributes to component"
            for attr_name, attr_value in attributes.iteritems():
                setattr(component, attr_name, attr_value)

            self.add_component(entity_id, component)

    def remove_component(self, entity_id, component_type):
        """Removes a specific entity component from the component database.

            Args:
                entity_id (long): The entity from which the component should be
                    removed.
                component_type (str): The the type of component to remove.

            Returns:
                The component which was removed or None if the component_type or
                entity does not exists.

        """
        component_entities = self.components.get(component_type)
        if component_entities is None:
            return None
        return component_entities.pop(entity_id, None)

    def remove_components(self, entity_id):
        """Calls remove component with the specified entity_id for each known
        component type"""
        for component_type in self.components:
            self.remove_component(entity_id, component_type)

    def get_component(self, entity_id, component_type):
        """Get an entity component.

            Returns:
                The component or None if the component does not exists

        """
        component_dict = self.components.get(component_type)
        if component_dict is None:
            return None
        return component_dict.get(entity_id)

    def get_all_of_type(self, component_type):
        """Get all components of the given type

            Returns:
                A dictionary containing all components of component_type
                or an empty dictionary, if none exist

        """
        component_dict = self.components.get(component_type)
        if component_dict is None:
            component_dict = {}
        return component_dict


class BlueprintManager:
    """Points the a blueprint file which contains information about the
    structure of an entity"""

    def create_configuration(self, blueprint):
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
