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
      this.thisWeek = new WeekView({ which: 'this', model: this.model })
      this.nextWeek = new WeekView({ which: 'next', model: this.model })
      this.planner = new PlannerView({ model:this.model })
    })

  WeekView = Backbone.View.extend(
    initialize: ()->
      if this.options.which is 'this'
        # render this week
        this.el = '#this_week'
        i = 0;
        while i < 7
          day = new DayView({ which:i,model:this.model })
          $(this.el).append(day.render().el)
          i += 1
      else if this.options.which is 'next'
        # render next week
        this.el = '#next_week'
        i = 7;
        while i < 14
          day = new DayView({ which:i,model:this.model })
          $(this.el).append(day.render().el)
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
    template: _.template($('#day_template').html()),
    events: {
      "click .herp"         : "show_inputter",
      "click .input_cover"  : "swap_back",
      "keypress .checker"      : "keypress_check"
    },
    initialize: ->
      # i is which day
      this.i = this.options.which
      this.weekday = weekdays[this.i%7]
      # render template
      if this.i < 7
        f_or_s = "First"
      else
        f_or_s = "Second"
      # get the tasks
      tasks_list = json_data.tasks[f_or_s][this.weekday]
      # for all tasks in this day, make a TaskView
      this.tasks = []
      for task_detail in tasks_list
        this.tasks.push(new TaskView({ model:this.model, detail:task_detail }))
    render: ->
      this.$el.addClass('weekday')
      this.$el.html(this.template({ day:json_data.two_weeks[this.i] }))
      for task in this.tasks
        $(this.$el.children()[0]).after(task.render())
      return this
    show_inputter: ->
      this_el = $(event.currentTarget)
      herp = $(this_el.children()[this_el.children().length-3])
      inputter = $(this_el.children()[this_el.children().length-2])
      cover = $(this_el.children()[this_el.children().length-1])
      herp.hide()
      inputter.show()
      cover.show()
    keypress_check: (e)->
      if (e.keyCode == 13)
        this.swap_back()
    swap_back: ->
      this_el = $(event.currentTarget)
      herp = $(this_el.children()[this_el.children().length-3])
      inputter = $(this_el.children()[this_el.children().length-2])
      cover = $(this_el.children()[this_el.children().length-1])
      # make new task and add to list
      task_name = inputter.children()[0].value
      task_duration = inputter.children()[2].value
      task_date = this_el.children()[0].innerHTML
      if task_name == ''
        herp.show()
        inputter.hide()
        cover.hide()
      else
        if task_duration == ''
          task_duration = '1 hour'
        # ajax post it to the server
        data =
          name: task_name
          date: task_date
          length: task_duration

        $.post "/addtask", data, (d, st, xr) ->
          console.log("Done")      

        herp.show()
        inputter.hide()
        cover.hide()
      
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
    events: {
      "click .toggle"       : "task_checked"
      "dblclick .task_name" : "edit_name"
      "click .input_cover"  : "swap_back"
      "keypress .edit"      : "check_key"
      "click .delete_task"  : "delete"

    }
    initialize: ->
      this.details = this.options.detail
    render: ->
      this.$el.addClass('task')
      this.$el.attr('id','task_'+this.details.id)
      if this.details.completed is true
        completed = 'checked'
      else
        completed = ''
      this.$el.html(this.template({ checked:completed, done:this.details.completed, name:this.details.name }))
      this.delegateEvents()
      return this.$el
    task_checked: ->
      checkbox = $($(event.currentTarget).children()[1])
      classList = checkbox.attr('class').split(/\s+/)
      checked = false
      $.each( classList, (index, item)->
        if item is 'checked'
          checked = true
      )
      id = event.currentTarget.id

      if not checked
        checkbox.addClass('checked')
        # submit check
        data =
          task_id: id
        $.post "/check", data, (d, st, xr) ->
          console.log("Marked as complete")
      else
        checkbox.removeClass('checked')
        # submit uncheck
        data =
          task_id: id
        $.post "/uncheck", data, (d, st, xr) ->
          console.log("Marked as complete")
    edit_name: ->
      this_el = $(event.currentTarget)
      task_name = $(this_el.children()[1])
      edit_field = $(this_el.children()[2])
      input_cover = $(this_el.children()[3])
      if edit_field.css('dispay','none')
        task_name.hide()  
        edit_field.show()
        input_cover.show()
    check_key: (e)->
      if (e.keyCode == 13)
        swap_back()
    swap_back: ->
      this_el = $(event.currentTarget)
      task_name = $(this_el.children()[1])
      edit_field = $(this_el.children()[2])
      input_cover = $(this_el.children()[3])
      # submit edit
      task_name.show()
      edit_field.hide()
      input_cover.hide()
    delete: ->
      id = event.currentTarget.id
      data =
        task_id: id
      $.post "/delete", data, (d, st, xr) ->
          console.log("Deleted")
      event.currentTarget.remove()

  )

  PlanView = Backbone.View.extend(
    
    # "drag" : "move"
    initialize: ->

    toggleDone: ->

    move: ->
  )

  # make the App
  App = new HomeView();