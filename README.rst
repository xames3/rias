.. Author: XA <xa@mes3.dev>
.. Created on: Saturday, June 22, 2023
.. Last updated on: Sunday, July 14 2024

Rias
====

Rias is a Machine Learning framework designed to streamline and simplify the
development of end-to-end Machine Learning workflows. Drawing inspiration from
industry frameworks like `Django`_, `Sphinx`_ and `Flask`_, Rias aims to offer
a comprehensive solution that caters to both novice and experienced Machine
Learning practitioners. By integrating the best development and design
principles, and leveraging community-driven development, Rias aspires to be the
go-to entry point for Machine Learning projects.

Why Rias?
---------

In the ever-evolving landscape of Machine Learning, there is a constant need
for adaptable and modular frameworks that can keep up with the rapid
advancements. While many powerful open-source tools exist, Rias stands out by
focusing on the following core strengths:

Extensibility
    The cornerstone of Rias is its robust agent system. Rias enables
    contributors to develop and share agents that extend its functionality,
    making it easy for users to customize their specific workflows without
    delving into the complexities of the framework.

Modularity and Adaptability
    Understanding the diverse and ever-changing landscape of Machine Learning,
    Rias is built with modularity at its core. This allows for seamless
    integration of various components and workflows, empowering users to adapt
    Rias to their unique requirements.

Community-Driven Development
    Rias thrives on the contributions from a global community of developers
    and data scientists. This collaborative approach ensures that Rias remains
    at the forefront of innovation, continuously evolving to meet the needs of
    its users.

Components
----------

Rias organizes its framework into a structured hierarchy that simplifies the
creation, management, and deployment of Machine Learning pipelines. Here's a
breakdown of the essential components:

Agent Manager
^^^^^^^^^^^^^

The top-level component responsible for overseeing multiple agents. It handles
lifecycle management, coordination, and orchestration of agents.

- **Responsibilities**:

  - Creating, configuring, and managing agents.
  - Monitoring agent health and performance.
  - Facilitating communication between agents and the overarching system.

Agents
^^^^^^

Core components that encapsulate workflows or pipelines. Agents manage the
execution of specific tasks within the MLOps framework and provide interfaces
for workflow management and execution.

- **Responsibilities**:

  - Managing one or more workflows or pipelines.
  - Serving as containers for tasks and transformations.
  - Providing interfaces for workflow management and execution.

Workflows
^^^^^^^^

Structured sequences of stages and tasks that define the end-to-end process
for a specific ML lifecycle phase (e.g., data preprocessing, model training,
deployment).

- **Responsibilities**:

  - Defining the flow of tasks and transformations.
  - Managing dependencies and execution order of stages and tasks.
  - Ensuring data passes through each step in the correct sequence.

Stages
^^^^^^

Subsections within a workflow or pipeline that group related tasks and
transformations, representing significant steps in the workflow.

- **Responsibilities**: Organize tasks for better management and monitoring.

Tasks
^^^^^

Individual units of work within a stage, performing specific operations such
as data loading, transformation, or model training.

- **Responsibilities**: Perform specific operations, process input data, and
  handle errors.

.. _Django: https://www.djangoproject.com/
.. _Sphinx: https://www.sphinx-doc.org/en/master/
.. _Flask: https://flask.palletsprojects.com/en/3.0.x/
