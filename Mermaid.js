classDiagram
    class Task {
        +str description
        +str due_time
        +date due_date
        +bool completed
        +str frequency
        +str priority
        +int duration_minutes
        +mark_complete()
    }

    class Pet {
        +str name
        +str species
        +str dietary_restrictions
        +str allergies
        +str health_conditions
        +list~Task~ tasks
        +add_task(task: Task)
        +edit_task(index: int, kwargs)
        +list_tasks() list~Task~
    }

    class Owner {
        +str name
        +list~Pet~ pets
        +add_pet(pet: Pet)
        +remove_pet(pet_name: str)
        +list_pets() list~Pet~
        +get_all_tasks() list~tuple~
    }

    class Scheduler {
        +Owner owner
        +sort_tasks() list~tuple~
        +sort_by_priority() list~tuple~
        +filter_tasks(completed, pet_name) list~tuple~
        +detect_conflicts() list~str~
        +handle_recurring(pet: Pet, task: Task)
    }

    Owner "1" --> "0..*" Pet : has
    Pet "1" --> "0..*" Task : has
    Owner "1" --> "1" Scheduler : uses
