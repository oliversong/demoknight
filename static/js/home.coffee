$ ->
  json_data = {}
  $.ajax({
    url: '/home_data',
    async: false,
    success: (data)->
      json_data = data
    }
  )

  console.log(json_data)

  # helpful day of the week zip
  weekdays = ['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday']

  # backbone models
  HomeModel = Backbone.Model.extend({
    initialize: ()->
      console.log("dashboard model initialized")
    })

  # backbone views
  HomeView = Backbone.View.extend({
    el: '#home',
    initialize: ()->
      this.model = new HomeModel()
      this.input = new InputView({ model: this.model })
      this.thisWeek = new WeekView({ which: 'this', model: this.model })
      this.nextWeek = new WeekView({ which: 'next', model: this.model })
      this.planner = new PlannerView({ model:this.model })
    })

  WeekView = Backbone.View.extend(
    initialize: ()->
      if this.options.which is 'this'
        # render this week
        this.el = $('#this_week')
        this.days = []
        i = 0;
        while i < 7
          day = new DayView({ which:i,model:this.model,parent:this.el })
          this.days.push(day)
          i += 1
      else if this.options.which is 'next'
        # render next week
        this.el = $('#next_week')
        this.days = []
        i = 7;
        while i < 14
          day = new DayView({ which:i,model:this.model,parent:this.el })
          this.days.push(day)
          i += 1
      else
        # what?
        console.log('You done goofed, son.')
  )

  PlannerView = Backbone.View.extend(
    el: '#planner'
    initialize: ->
      this.plandays = []
      i = 0;
      while i < 7
        planday = new PlanDayView({ which:i, model:this.model })
        this.plandays.push(planday)
        i += 1

    render: ->
  )

  DayView = Backbone.View.extend(
    template: _.template($('#day_template').html())
    initialize: ->
      i = this.options.which
      this.parent = this.options.parent
      # for all tasks in this day, make a TaskView
      this.tasks = []
      weekday = weekdays[i%7]
      segment = this.template({ day:json_data.two_weeks[i] })
      if i < 7
        f_or_s = "First"
      else
        f_or_s = "Second"
      tasks_list = json_data.tasks[f_or_s][weekday]
      for task_detail in tasks_list
        this.tasks.push(new TaskView({ model:this.model, detail:task_detail }))
      this.render(segment)

    render: (segment) ->
      this.parent.append(segment)
      for task in this.tasks
        this.$el.append(task.render())
      return this
  )

  PlanDayView = Backbone.View.extend(
    template: _.template($('#planday_template').html())
    initialize: ->
      i = this.options.which
      this.plans = []
      weekday = weekdays[i]
      for plan_detail in json_data.planned[weekday]
        plan = new PlanView({ model:this.model, detail:plan_detail })
        this.plans.push(plan)
      this.render(i)
    render: (i) ->
      $('#planner').append(this.template({ day:json_data.two_weeks[i] }))
      return this
  )

  TaskView = Backbone.View.extend(
    template: _.template($("#task_template").html())
    initialize: ->
      this.details = this.options.detail
    render: ->
      this.$el.html(this.template({ done:this.details.completed, name:this.details.name }))
      this.delegateEvents()
      return this
  )

  PlanView = Backbone.View.extend(
    
    # "drag" : "move"
    initialize: ->

    toggleDone: ->

    move: ->
  )
  InputView = Backbone.View.extend(
    el: $('#input_container')
    template: _.template($('#inputter_template').html())
    events: {
      "click .add_task"   : "new_task"
    }

    initialize: ->
      this.render()
      nowTemp = new Date()
      now = new Date(nowTemp.getFullYear(), nowTemp.getMonth(), nowTemp.getDate(), 0, 0, 0, 0)
      $('#dawg').datepicker(onRender: (date) ->
        (if date.valueOf() < now.valueOf() then "disabled" else "")
      )

      this.task_name = this.$("#task_name")
      this.task_date = this.$("#task_date")
      this.task_length = this.$("#task_length")

    render: ->
      $(this.el).html(this.template({ today:json_data.today }));

      return this

    new_task: ->
      # ajax post it to the server
      data =
        name: @task_name.val()
        date: @task_date.val()
        length: @task_length.val()

      # trigger event "task_create name date length"
      this.model.trigger('new_task',data)

      $.post "/addtask", data, (d, st, xr) ->
        console.log("Done")
  )

  # make the App
  App = new HomeView();