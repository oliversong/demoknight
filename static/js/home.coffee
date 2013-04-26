$ ->
  nowTemp = new Date()
  now = new Date(nowTemp.getFullYear(), nowTemp.getMonth(), nowTemp.getDate(), 0, 0, 0, 0)
  checkin = $("#taskDate").datepicker(onRender: (date) ->
    (if date.valueOf() < now.valueOf() then "disabled" else "")
  )
  console.log "datepicker init"

  json_data = {}
  $.ajax({
    url: '/home_data',
    async: false,
    success: (data)->
      json_data = data
    }
  )
  console.log "Get data"

  # backbone models
  HomeModel = Backbone.Model.extend({
    initialize: ()->
      console.log("dashboard model initialized")
    })
  TaskModel = Backbone.Model.extend({

    })
  PlanModel = Backbone.Model.extend({

    })
  DayModel = Backbone.Model.extend({

    })
  PlannerModel = Backbone.Model.extend({

    })

  # backbone views
  HomeView = Backbone.View.extend({
    el: '#home',
    initialize: ()->
      this.model = new HomeModel
      this.input = new InputView
      this.thisWeek = new WeekView({ type: 'this', model: this.model})
      this.nextWeek = new WeekView({ type: 'next', model: this.model})
      this.planner = new PlannerView
    })

  WeekView = Backbone.View.extend(
    initialize: (spec)->
      if this.type is 'this'
        # render this week
      else if this.type is 'next'
        # render next week
      else
        # what?

  )
  PlannerView = Backbone.View.extend(
    el: $(".planner")
    initialize: ->

    render: ->
  )
  DayView = Backbone.View.extend(
    el: $(".day")
    initialize: ->

    render: ->
  )
  TaskView = Backbone.View.extend(
    el: $(".task")
    model: TaskModel
    template: _.template($("#task_template").html())
    events:
      "click .toggle": "toggleDone"

    initialize: ->
      @listenTo @model, "change", @render
      @listenTo @model, "destroy", @remove
  )

  PlanView = Backbone.View.extend(
    el: $(".plan")
    events:
      "click .toggle": "toggleDone"

    
    # "drag" : "move"
    initialize: ->

    toggleDone: ->

    move: ->
  )
  InputView = Backbone.View.extend(
    el: $(".task_input")
    events:
      "keypress .add_task": "create"

    initialize: ->
      @home = @task_name = @$(".task_name")
      @task_date = @$(".task_date")
      @task_length = @$(".task_length")

    create: ->
      
      # trigger event "task_create name date length"
      
      # ajax post it to the server
      data =
        name: @task_name
        date: @task_date
        length: @task_length

      $.post "/addtask", data, (d, st, xr) ->
        "Done"

  # make the App
  App = new HomeView();
  )
